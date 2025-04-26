import pygame
import sys
import io
from multiprocessing import Process, Queue
from queue import Empty
import time
from .theme import current_theme
import psutil  # Add at top with other imports

class Window:
    def __init__(self, title, x, y, width, height):
        self.title = title
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        self.dragging = False
        self.drag_offset = (0, 0)
        self.active = True
        self.title_bar_height = 25
        self.close_button = pygame.Rect(width - 25, 0, 25, 25)
        
    def draw(self, screen):
        # Draw window background
        self.surface.fill(current_theme.window_bg)
        
        # Draw title bar - different color when active
        title_color = current_theme.window_title_active if self.active else current_theme.window_title_inactive
        pygame.draw.rect(self.surface, title_color, (0, 0, self.width, self.title_bar_height))
        
        # Draw title text
        font = pygame.font.Font(None, 24)
        title_text = font.render(self.title, True, current_theme.title_text)
        self.surface.blit(title_text, (5, 5))
        
        # Draw close button
        pygame.draw.rect(self.surface, (255, 0, 0), self.close_button)
        pygame.draw.line(self.surface, current_theme.text, 
                        (self.width - 22, 5), (self.width - 7, 20), 2)  # Moved 2px left
        pygame.draw.line(self.surface, current_theme.text, 
                        (self.width - 7, 5), (self.width - 22, 20), 2)  # Moved 2px left
        
        # Draw window content
        self.draw_content()
        
        # Draw the window to the screen
        screen.blit(self.surface, (self.x, self.y))
        
        # Draw active window border
        border_color = current_theme.window_border_active if self.active else current_theme.window_border_inactive
        pygame.draw.rect(screen, border_color, 
                       (self.x - 2, self.y - 2, self.width + 4, self.height + 4), 2)
    
    def draw_content(self):
        # Override this in subclasses
        pass
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            window_pos = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
            
            # Check if clicking close button
            if self.close_button.collidepoint(window_pos) and window_pos[1] < self.title_bar_height:
                self.close()  # New method for proper closing
                return False
            
            # Create title bar rect for proper bounds checking
            title_bar_rect = pygame.Rect(0, 0, self.width - self.close_button.width, self.title_bar_height)
            if title_bar_rect.collidepoint(window_pos):
                self.dragging = True
                self.drag_offset = window_pos
                return True
            
            # Window was clicked somewhere - activate it
            if 0 <= window_pos[0] <= self.width and 0 <= window_pos[1] <= self.height:
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_pos = pygame.mouse.get_pos()
            self.x = mouse_pos[0] - self.drag_offset[0]
            self.y = mouse_pos[1] - self.drag_offset[1]
            return True
            
        return True

    def close(self):
        # Base implementation - override in subclasses if needed
        self.active = False

    def update(self):
        # Base update method - override in subclasses if needed
        pass

class TerminalWindow(Window):
    def __init__(self, title, x, y, width, height):
        super().__init__(title, x, y, width, height)
        self.output_buffer = []
        self.font = pygame.font.Font(None, 24)
        self.text_color = current_theme.terminal_text
        self.background_color = current_theme.terminal_bg
        self.line_height = 20
        self.output_queue = Queue()
        self.max_lines = (height - self.title_bar_height - 30) // self.line_height  # Adjust for action bar
        
        # Action bar buttons
        self.action_bar_height = 30
        self.clear_button = pygame.Rect(5, self.title_bar_height, 60, 25)
        self.copy_button = pygame.Rect(70, self.title_bar_height, 60, 25)
        
    def add_output(self, text):
        lines = text.split('\n')
        for line in lines:
            self.output_buffer.append(line)
            if len(self.output_buffer) > self.max_lines:
                self.output_buffer.pop(0)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            local_pos = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
            
            if self.clear_button.collidepoint(local_pos):
                self.output_buffer = []
                return True
            elif self.copy_button.collidepoint(local_pos):
                # Copy output to clipboard
                output_text = '\n'.join(self.output_buffer)
                pygame.scrap.put(pygame.SCRAP_TEXT, output_text.encode())
                return True
                
        return super().handle_event(event)

    def draw_content(self):
        # Draw action bar background
        pygame.draw.rect(self.surface, current_theme.button_bg, 
                        (0, self.title_bar_height, self.width, self.action_bar_height))
        
        # Draw action buttons
        pygame.draw.rect(self.surface, current_theme.button_bg, self.clear_button)
        pygame.draw.rect(self.surface, current_theme.button_bg, self.copy_button)
        
        # Draw button text
        clear_text = self.font.render('Clear', True, current_theme.title_text)
        copy_text = self.font.render('Copy', True, current_theme.title_text)
        self.surface.blit(clear_text, (10, self.title_bar_height + 5))
        self.surface.blit(copy_text, (75, self.title_bar_height + 5))
        
        # Draw terminal content
        pygame.draw.rect(self.surface, self.background_color, 
                        (0, self.title_bar_height + self.action_bar_height, 
                         self.width, self.height - self.title_bar_height - self.action_bar_height))
        
        # Draw output text
        y = self.title_bar_height + self.action_bar_height + 5
        for line in self.output_buffer:
            text_surface = self.font.render(line, True, self.text_color)
            self.surface.blit(text_surface, (5, y))
            y += self.line_height

        # Process any pending output
        while not self.output_queue.empty():
            self.add_output(self.output_queue.get_nowait())

class PyAppWindow(Window):
    def __init__(self, title, x, y, width, height, app_code, window_manager):  # Add window_manager param
        super().__init__(title, x, y, width, height)
        self.app_code = app_code
        self.running = True
        self.content_rect = pygame.Rect(5, self.title_bar_height + 5, 
                                      width - 10, height - self.title_bar_height - 10)
        self.clock = pygame.time.Clock()
        self.last_update = pygame.time.get_ticks()
        
        # Store window manager reference
        self.window_manager = window_manager
        
        # Create namespace for the app
        self.namespace = {
            'pygame': pygame,
            'psutil': psutil,  # Add psutil to namespace
            'random': __import__('random'),
            'math': __import__('math'),
            'time': __import__('time'),
            'sys': sys,
            'io': io,
            'os': __import__('os'),
            '__name__': '__main__',
            '__builtins__': __builtins__,
            'running': True,
            'delta_time': 0.0,
            'api': window_manager,  # Pass the actual window manager instance
            'is_taskmanager': 'tskmngr.pya' in title.lower()  # Special flag for task manager
        }
        
        try:
            # Execute the app code to define functions
            exec(self.app_code, self.namespace)
            
            if 'main' not in self.namespace:
                raise Exception("PyOS App must define a main(screen, recSt) function")
                
            # Initialize any state the app needs
            if 'init' in self.namespace:
                self.namespace['init'](self.content_rect)
        except Exception as e:
            print(f"Error initializing PyOS App: ")
            __import__('traceback').print_exc()
            self.running = False
    
    def handle_event(self, event):
        if not self.running:
            return False
            
        # Handle window events first
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            window_pos = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
            
            # Check if clicking close button
            if self.close_button.collidepoint(window_pos) and window_pos[1] < self.title_bar_height:
                self.close()
                return False
            
            # Create title bar rect for proper bounds checking
            title_bar_rect = pygame.Rect(0, 0, self.width - self.close_button.width, self.title_bar_height)
            if title_bar_rect.collidepoint(window_pos):
                self.dragging = True
                self.drag_offset = window_pos
                return True
            
            # Rest of mouse handling for app content
            # Create an adjusted event for the app's coordinate space
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if hasattr(event, 'pos'):
                    rel_x = event.pos[0] - self.x - self.content_rect.x
                    rel_y = event.pos[1] - self.y - self.content_rect.y
                    if 0 <= rel_x < self.content_rect.width and 0 <= rel_y < self.content_rect.height:
                        event_dict = {'pos': (rel_x, rel_y)}
                        if event.type == pygame.MOUSEMOTION:
                            event_dict['rel'] = event.rel
                            event_dict['buttons'] = event.buttons
                        else:
                            event_dict['button'] = event.button
                        adj_event = pygame.event.Event(event.type, event_dict)
                        # Forward event to app if it has an event handler
                        if 'handle_event' in self.namespace:
                            try:
                                self.namespace['handle_event'](adj_event)
                            except Exception as e:
                                #print(f"Error in app event handler: {str(e)}")
                                print(f"Error in app event handler:")
                                __import__('traceback').print_exc()
            elif event.type == pygame.KEYDOWN:
                # Forward keyboard events to app if it has an event handler
                if 'handle_event' in self.namespace:
                    try:
                        self.namespace['handle_event'](event)
                    except Exception as e:
                        #print(f"Error in app event handler: {str(e)}")
                        print(f"Error in app event handler:")
                        __import__('traceback').print_exc()
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_pos = pygame.mouse.get_pos()
            self.x = mouse_pos[0] - self.drag_offset[0]
            self.y = mouse_pos[1] - self.drag_offset[1]
            return True
        
        return True

    def close(self):
        if 'close' in self.namespace:
            self.namespace['close']()
        self.running = False
        self.active = False

    def draw(self, screen):
        if not self.running:
            return
            
        try:
            # Calculate delta time
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - self.last_update) / 1000.0  # Convert to seconds
            self.last_update = current_time
            self.namespace['delta_time'] = delta_time
            
            # Draw window frame
            self.surface.fill(current_theme.window_bg)
            pygame.draw.rect(self.surface, current_theme.window_title_active if self.active else current_theme.window_title_inactive, 
                           (0, 0, self.width, self.title_bar_height))
            
            # Draw title text
            font = pygame.font.Font(None, 24)
            title_text = font.render(self.title, True, current_theme.title_text)
            self.surface.blit(title_text, (5, 5))
            
            # Draw close button
            pygame.draw.rect(self.surface, (255, 0, 0), self.close_button)
            pygame.draw.line(self.surface, current_theme.text, 
                           (self.width - 22, 5), (self.width - 7, 20), 2)  # Moved 2px left
            pygame.draw.line(self.surface, current_theme.text, 
                           (self.width - 7, 5), (self.width - 22, 20), 2)  # Moved 2px left
            
            # Draw window border
            border_color = current_theme.window_border_active if self.active else current_theme.window_border_inactive
            pygame.draw.rect(self.surface, border_color, (0, 0, self.width, self.height), 2)
            
            # Draw window to screen first
            screen.blit(self.surface, (self.x, self.y))
            
            # Calculate content area in screen coordinates
            content_screen_rect = pygame.Rect(
                self.x + self.content_rect.x,
                self.y + self.content_rect.y,
                self.content_rect.width,
                self.content_rect.height
            )
            
            # Let the app draw directly to the screen in its area
            if 'main' in self.namespace:
                self.namespace['main'](screen, content_screen_rect)
                
            # Maintain consistent frame rate
            self.clock.tick(60)
            
        except Exception as e:
            #print(f"Error in app main loop: {str(e)}")
            print(f"Error in app main loop:")
            __import__('traceback').print_exc()
            self.running = False

    def _get_window_manager(self):
        return self.window_manager

class WindowManager:
    def __init__(self, screen):
        self.screen = screen
        self.windows = []
        self.windows_to_remove = []  # Add this to track windows that need removal
        self.last_frame_time = time.time()
        self.frame_times = []  # Store last 60 frame times
        
    def create_window(self, window):
        self.windows.append(window)
        self.activate_window(window)
        
    def activate_window(self, window):
        # Deactivate all windows
        for w in self.windows:
            w.active = False
        # Activate the selected window
        window.active = True
        
    def bring_to_front(self, window):
        if window in self.windows:
            self.windows.remove(window)
            self.windows.append(window)
            self.activate_window(window)
            
    def handle_event(self, event):
        # Handle events in reverse order (top to bottom)
        for window in reversed(self.windows):
            result = window.handle_event(event)
            if result is False:  # Window wants to close
                print(f"Closing window: {window.title}")
                self.windows_to_remove.append(window)
            return True
        return False
        
    def update(self):
        # Update FPS calculation
        current_time = time.time()
        delta = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        self.frame_times.append(delta)
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
            
        # Remove any windows marked for removal
        for window in self.windows_to_remove:
            if window in self.windows:
                self.windows.remove(window)
        self.windows_to_remove.clear()
        
        # Update all windows
        for window in self.windows:
            window.update()
            
    def draw(self):
        # Draw all windows in order (bottom to top)
        for window in self.windows:
            window.draw(self.screen)

    def create_api(self):
        """Create API object with limited system calls for apps"""
        return {
            'spawn_window': self.create_window,
            'close_window': lambda window: self.windows_to_remove.append(window),
            'windows': self.windows,  # Direct access to windows list
            'bring_to_front': self.bring_to_front,
            'get_performance': self.get_performance,  # Match the method name
            'terminate_window': self.terminate_window
        }
    
    def get_performance(self):  # Rename to match API
        """Get system performance metrics"""
        try:
            # Calculate average FPS from frame times
            if self.frame_times:
                avg_frame_time = sum(self.frame_times) / len(self.frame_times)
                current_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            else:
                current_fps = 0
                
            metrics = {
                'cpu': psutil.cpu_percent(interval=0.1),
                'memory': psutil.virtual_memory().percent,
                'window_count': len(self.windows),
                'fps': int(current_fps)
            }
            return metrics
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return {
                'cpu': 0,
                'memory': 0,
                'window_count': len(self.windows),
                'fps': 0
            }

    def terminate_window(self, window, caller_window=None):
        """Special method for terminating windows with proper permissions"""
        if caller_window and 'tskmngr.pya' in caller_window.title.lower():
            # Task Manager can terminate any window, including itself
            self.windows_to_remove.append(window)
            return True
        return False