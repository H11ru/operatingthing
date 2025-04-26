import pygame
import sys
import io
from threading import Thread
from .window_manager import Window, TerminalWindow, PyAppWindow
from .theme import current_theme

class TaskbarButton:
    def __init__(self, x, y, width, height, text, window=None, is_power=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.window = window
        self.is_power = is_power
        self.is_hovered = False
        self.font = pygame.font.Font(None, 20)
        
    def draw(self, screen):
        color = current_theme.taskbar_button
        if self.is_hovered:
            color = current_theme.taskbar_button_hover
            
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, current_theme.taskbar_border, self.rect, 1)
        
        text_surface = self.font.render(self.text, True, current_theme.text)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class Taskbar:
    def __init__(self, screen_width, screen_height):
        self.height = 30
        self.y = screen_height - self.height
        self.width = screen_width
        self.rect = pygame.Rect(0, self.y, self.width, self.height)
        self.buttons = []
        
        # Create power button
        power_width = 80
        self.power_button = TaskbarButton(5, self.y + 2, power_width, self.height - 4, "Shutdown...", is_power=True)
        
    def update_window_buttons(self, windows):
        # Clear existing window buttons
        self.buttons.clear()
        
        # Create buttons for each window
        button_width = 150
        x = 90  # Increased from 80 to give more space after power button
        for window in windows:
            if x + button_width > self.width:
                break
            button = TaskbarButton(x, self.y + 2, button_width, self.height - 4, window.title, window)
            self.buttons.append(button)
            x += button_width + 5
            
    def handle_event(self, event, window_manager):
        if event.type == pygame.MOUSEMOTION:
            # Update hover states
            mouse_pos = event.pos
            self.power_button.is_hovered = self.power_button.rect.collidepoint(mouse_pos)
            for button in self.buttons:
                button.is_hovered = button.rect.collidepoint(mouse_pos)
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click only
            mouse_pos = event.pos
            if self.power_button.rect.collidepoint(mouse_pos):
                window_manager.quit_requested = True
                pygame.event.post(pygame.event.Event(pygame.QUIT))  # Force quit event
                return True
                
            for button in self.buttons:
                if button.rect.collidepoint(mouse_pos):
                    window_manager.bring_to_front(button.window)
                    return True
        return False
    
    def draw(self, screen):
        # Draw taskbar background
        pygame.draw.rect(screen, current_theme.taskbar_bg, self.rect)
        pygame.draw.line(screen, current_theme.taskbar_border, 
                        (0, self.y), (self.width, self.y))
        
        # Draw power button
        self.power_button.draw(screen)
        
        # Draw window buttons
        for button in self.buttons:
            button.draw(screen)

class FileIcon:
    def __init__(self, name, x, y, file_type):
        self.name = name
        self.x = x
        self.y = y
        self.width = 64
        self.height = 64
        self.file_type = file_type
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def draw(self, screen):
        # Draw icon with theme colors
        pygame.draw.rect(screen, current_theme.button_bg, self.rect)
        pygame.draw.rect(screen, current_theme.accent, self.rect, 2)  # Green outline
        
        # Draw icon text
        font = pygame.font.Font(None, 20)
        text = font.render(self.name, True, current_theme.text)
        text_rect = text.get_rect(centerx=self.x + self.width//2, top=self.y + self.height + 5)
        screen.blit(text, text_rect)

class TextEditorWindow(Window):
    def __init__(self, title, x, y, width, height, content, filesystem=None, filename=None):
        super().__init__(title, x, y, width, height)
        self.content = content
        self.font = pygame.font.Font(None, 24)
        self.text_color = current_theme.editor_text
        self.line_height = 25
        self.scroll_y = 0
        self.cursor_pos = [0, 0]  # [line, char]
        self.selection_start = None
        self.lines = content.split('\n')
        self.filesystem = filesystem
        self.filename = filename
        
        # Add save button in title bar with wider width for "SAVE" text
        self.save_button = pygame.Rect(self.width - 80, 0, 50, 25)
        
        # Editor state
        self.blink_timer = 0
        self.show_cursor = True
        self.last_click_time = 0
        self.click_count = 0
        self.last_click_pos = None
        
        # Add key repeat state
        self.key_repeat_delay = 500  # Initial delay in ms
        self.key_repeat_interval = 50  # Repeat interval in ms
        self.key_held_since = 0
        self.last_key_repeat = 0
        self.held_key = None
        self.held_unicode = None  # Store unicode character for letter keys
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            window_pos = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)
            
            # First check if window was clicked anywhere (for activation)
            if 0 <= window_pos[0] <= self.width and 0 <= window_pos[1] <= self.height:
                should_activate = True
            
            # Check save button first
            if self.save_button.collidepoint(window_pos) and window_pos[1] < self.title_bar_height:
                self.save_file()
                return True
                
            # Check close button
            if self.close_button.collidepoint(window_pos) and window_pos[1] < self.title_bar_height:
                return False  # Tell window manager to remove this window

            # Let parent handle close button first
            if window_pos[1] < self.title_bar_height:
                result = super().handle_event(event)
                if result == False:  # Window should close
                    return False
                return True
            
            # Handle text editor specific mouse events
            if window_pos[1] >= self.title_bar_height:
                # Handle mouse wheel scrolling
                if event.button == 4:  # Mouse wheel up
                    self.scroll_y = max(0, self.scroll_y - self.line_height)
                    return True
                elif event.button == 5:  # Mouse wheel down
                    max_scroll = max(0, len(self.lines) * self.line_height - (self.height - self.title_bar_height))
                    self.scroll_y = min(max_scroll, self.scroll_y + self.line_height)
                    return True
                    
                # Handle text selection
                local_y = window_pos[1] - self.title_bar_height + self.scroll_y
                line_idx = int(local_y // self.line_height)
                if 0 <= line_idx < len(self.lines):
                    # Calculate character position
                    local_x = window_pos[0] - 5
                    char_pos = 0
                    line = self.lines[line_idx]
                    for i, char in enumerate(line):
                        char_width = self.font.render(char, True, self.text_color).get_width()
                        if local_x < char_width / 2:
                            break
                        local_x -= char_width
                        char_pos = i + 1
                        
                    # Handle multiple clicks and shift-click
                    current_time = pygame.time.get_ticks()
                    if (current_time - self.last_click_time < 500 and 
                        self.last_click_pos == (line_idx, char_pos)):
                        self.click_count += 1
                        if self.click_count == 2:
                            # Double click - select word
                            self.select_word(line_idx, char_pos)
                        elif self.click_count == 3:
                            # Triple click - select line
                            self.select_line(line_idx)
                    else:
                        self.click_count = 1
                        if event.button == pygame.BUTTON_LEFT:
                            # Handle shift-click for selection
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                if self.selection_start is None:
                                    self.selection_start = self.cursor_pos.copy()
                            else:
                                self.selection_start = None
                            self.cursor_pos = [line_idx, char_pos]
                    
                    self.last_click_time = current_time
                    self.last_click_pos = (line_idx, char_pos)
                    self.show_cursor = True
                    self.blink_timer = 0
                    
                return True
            
        elif event.type == pygame.MOUSEBUTTONUP:
            # Always let parent window handle mouse up events
            return super().handle_event(event)
        
        elif event.type == pygame.KEYDOWN and self.active:
            self.held_key = event.key
            self.held_unicode = event.unicode  # Store unicode for letter keys
            self.key_held_since = pygame.time.get_ticks()
            self.handle_key_input(event)
            
        elif event.type == pygame.KEYUP and self.active:
            if event.key == self.held_key:
                self.held_key = None
                self.held_unicode = None
                
        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:  # Left button
                window_pos = (event.pos[0] - self.x, event.pos[1] - self.y)
                if window_pos[1] >= self.title_bar_height:
                    if self.selection_start is None:
                        self.selection_start = self.cursor_pos.copy()
                    local_y = window_pos[1] - self.title_bar_height + self.scroll_y
                    line_idx = max(0, min(int(local_y // self.line_height), len(self.lines) - 1))
                    local_x = window_pos[0] - 5
                    char_pos = 0
                    line = self.lines[line_idx]
                    for i, char in enumerate(line):
                        char_width = self.font.render(char, True, self.text_color).get_width()
                        if local_x < char_width / 2:
                            break
                        local_x -= char_width
                        char_pos = i + 1
                    self.cursor_pos = [line_idx, char_pos]
            super().handle_event(event)
            
        return True
    
    def update(self):
        # Handle key repeat for all keys
        if self.held_key is not None:
            current_time = pygame.time.get_ticks()
            if current_time - self.key_held_since > self.key_repeat_delay:
                if current_time - self.last_key_repeat > self.key_repeat_interval:
                    self.last_key_repeat = current_time
                    # Create a fake event for the held key
                    fake_event = pygame.event.Event(pygame.KEYDOWN, {
                        'key': self.held_key,
                        'mod': pygame.key.get_mods(),
                        'unicode': self.held_unicode or ''  # Include unicode for letter keys
                    })
                    self.handle_key_input(fake_event)
    
    def handle_key_input(self, event):
        if event.key == pygame.K_RETURN:
            self.insert_text('\n')
        elif event.key == pygame.K_BACKSPACE:
            if self.selection_start is not None:
                self.delete_selection()
            elif self.cursor_pos[1] > 0:
                # Delete character before cursor
                line = self.lines[self.cursor_pos[0]]
                self.lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]-1] + line[self.cursor_pos[1]:]
                self.cursor_pos[1] -= 1
            elif self.cursor_pos[0] > 0:
                # Join with previous line
                prev_line_len = len(self.lines[self.cursor_pos[0]-1])
                self.lines[self.cursor_pos[0]-1] += self.lines[self.cursor_pos[0]]
                self.lines.pop(self.cursor_pos[0])
                self.cursor_pos[0] -= 1
                self.cursor_pos[1] = prev_line_len
        elif event.key == pygame.K_DELETE:
            if self.selection_start is not None:
                self.delete_selection()
            elif self.cursor_pos[1] < len(self.lines[self.cursor_pos[0]]):
                # Delete character after cursor
                line = self.lines[self.cursor_pos[0]]
                self.lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]] + line[self.cursor_pos[1]+1:]
            elif self.cursor_pos[0] < len(self.lines) - 1:
                # Join with next line
                self.lines[self.cursor_pos[0]] += self.lines[self.cursor_pos[0]+1]
                self.lines.pop(self.cursor_pos[0]+1)
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            if event.mod & pygame.KMOD_SHIFT:
                if self.selection_start is None:
                    self.selection_start = self.cursor_pos.copy()
            else:
                self.selection_start = None
                
            if event.key == pygame.K_LEFT:
                if self.cursor_pos[1] > 0:
                    self.cursor_pos[1] -= 1
                elif self.cursor_pos[0] > 0:
                    self.cursor_pos[0] -= 1
                    self.cursor_pos[1] = len(self.lines[self.cursor_pos[0]])
            elif event.key == pygame.K_RIGHT:
                if self.cursor_pos[1] < len(self.lines[self.cursor_pos[0]]):
                    self.cursor_pos[1] += 1
                elif self.cursor_pos[0] < len(self.lines) - 1:
                    self.cursor_pos[0] += 1
                    self.cursor_pos[1] = 0
            elif event.key == pygame.K_UP:
                if self.cursor_pos[0] > 0:
                    self.cursor_pos[0] -= 1
                    self.cursor_pos[1] = min(self.cursor_pos[1], len(self.lines[self.cursor_pos[0]]))
            elif event.key == pygame.K_DOWN:
                if self.cursor_pos[0] < len(self.lines) - 1:
                    self.cursor_pos[0] += 1
                    self.cursor_pos[1] = min(self.cursor_pos[1], len(self.lines[self.cursor_pos[0]]))
        elif event.unicode and event.unicode >= ' ':
            self.insert_text(event.unicode)
            
        self.show_cursor = True
        self.blink_timer = 0
    
    def insert_text(self, text):
        if self.selection_start is not None:
            self.delete_selection()
        
        if text == '\n':
            # Split line at cursor
            line = self.lines[self.cursor_pos[0]]
            self.lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]]
            self.lines.insert(self.cursor_pos[0] + 1, line[self.cursor_pos[1]:])
            self.cursor_pos[0] += 1
            self.cursor_pos[1] = 0
        else:
            # Insert character at cursor
            line = self.lines[self.cursor_pos[0]]
            self.lines[self.cursor_pos[0]] = line[:self.cursor_pos[1]] + text + line[self.cursor_pos[1]:]
            self.cursor_pos[1] += len(text)
    
    def delete_selection(self):
        if self.selection_start is None:
            return
            
        # Ensure selection_start is before cursor_pos
        if (self.selection_start[0] > self.cursor_pos[0] or 
            (self.selection_start[0] == self.cursor_pos[0] and 
             self.selection_start[1] > self.cursor_pos[1])):
            self.selection_start, self.cursor_pos = self.cursor_pos, self.selection_start
            
        if self.selection_start[0] == self.cursor_pos[0]:
            # Selection on same line
            line = self.lines[self.selection_start[0]]
            self.lines[self.selection_start[0]] = (
                line[:self.selection_start[1]] + line[self.cursor_pos[1]:])
            self.cursor_pos = self.selection_start
        else:
            # Selection spans multiple lines
            first_line = self.lines[self.selection_start[0]]
            last_line = self.lines[self.cursor_pos[0]]
            self.lines[self.selection_start[0]] = (
                first_line[:self.selection_start[1]] + last_line[self.cursor_pos[1]:])
            del self.lines[self.selection_start[0]+1:self.cursor_pos[0]+1]
            self.cursor_pos = self.selection_start
            
        self.selection_start = None
    
    def select_word(self, line_idx, char_pos):
        line = self.lines[line_idx]
        # Find word boundaries
        start = char_pos
        while start > 0 and line[start-1].isalnum():
            start -= 1
        end = char_pos
        while end < len(line) and line[end].isalnum():
            end += 1
        self.selection_start = [line_idx, start]
        self.cursor_pos = [line_idx, end]
    
    def select_line(self, line_idx):
        self.selection_start = [line_idx, 0]
        self.cursor_pos = [line_idx, len(self.lines[line_idx])]
    
    def save_file(self):
        if self.filesystem and self.filename:
            content = '\n'.join(self.lines)
            self.filesystem.create_file(self.filename, content)
    
    def draw(self, screen):
        super().draw(screen)
        
        # Update cursor blink
        self.blink_timer += 1
        if self.blink_timer >= 30:  # Blink every 30 frames
            self.show_cursor = not self.show_cursor
            self.blink_timer = 0

    def draw_content(self):
        # Draw text editor background
        pygame.draw.rect(self.surface, current_theme.editor_bg, 
                        (0, self.title_bar_height, self.width, self.height - self.title_bar_height))
        
        # Draw save button with "SAVE" text
        pygame.draw.rect(self.surface, current_theme.button_bg, self.save_button)
        pygame.draw.rect(self.surface, current_theme.accent, self.save_button, 2)  # Green outline
        save_text = self.font.render('SAVE', True, current_theme.text)
        self.surface.blit(save_text, (self.width - 75, 5))
        
        # Draw text content
        y = self.title_bar_height + 5 - self.scroll_y
        for line_idx, line in enumerate(self.lines):
            if y + self.line_height >= self.title_bar_height:
                # Draw selection highlight
                if self.selection_start is not None:
                    sel_start = self.selection_start
                    sel_end = self.cursor_pos
                    if sel_start[0] > sel_end[0] or (sel_start[0] == sel_end[0] and sel_start[1] > sel_end[1]):
                        sel_start, sel_end = sel_end, sel_start
                        
                    if sel_start[0] <= line_idx <= sel_end[0]:
                        start_x = 5
                        if line_idx == sel_start[0]:
                            start_x += self.font.render(line[:sel_start[1]], True, self.text_color).get_width()
                            
                        end_x = self.width - 5
                        if line_idx == sel_end[0]:
                            end_x = 5 + self.font.render(line[:sel_end[1]], True, self.text_color).get_width()
                            
                        pygame.draw.rect(self.surface, current_theme.editor_selection,
                                       (start_x, y, end_x - start_x, self.line_height))
                
                # Draw text
                text_surface = self.font.render(line, True, current_theme.editor_text)
                self.surface.blit(text_surface, (5, y))
                
                # Draw cursor
                if line_idx == self.cursor_pos[0] and self.show_cursor and self.active:
                    cursor_x = 5 + self.font.render(line[:self.cursor_pos[1]], True, self.text_color).get_width()
                    pygame.draw.line(self.surface, current_theme.editor_cursor,
                                   (cursor_x, y), (cursor_x, y + self.line_height), 2)
            y += self.line_height

    def close(self):
        print("I was closed.") # This print statement never printed..?
        # Override close to ensure window is removed, not just deactivated
        return False  # Tell window manager to remove this window

class Desktop:
    def __init__(self, window_manager, app_manager):
        self.window_manager = window_manager
        self.app_manager = app_manager
        self.icons = []
        self.taskbar = Taskbar(window_manager.screen.get_width(), 
                             window_manager.screen.get_height())
        self.refresh_icons()

    def refresh_icons(self):
        self.icons = []
        files = self.app_manager.list_files()
        for i, (name, file_type) in enumerate(files):
            x = 20 + (i % 5) * 100
            y = 20 + (i // 5) * 100
            self.icons.append(FileIcon(name, x, y, file_type))

    def handle_event(self, event):
        self.taskbar.handle_event(event, self.window_manager)
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if pos[1] < self.taskbar.y:  # Only handle clicks above taskbar
                for icon in self.icons:
                    if icon.rect.collidepoint(pos):
                        self.open_file(icon.name, icon.file_type)

    def open_file(self, filename, file_type):
        if file_type == "py":
            result = self.app_manager.execute_file(filename)
            if isinstance(result, str):  # If it's a Python file path
                terminal = TerminalWindow(f"Terminal - {filename}", 100, 100, 600, 400)
                self.window_manager.create_window(terminal)
                
                def run_script():
                    # Redirect stdout to capture output
                    old_stdout = sys.stdout
                    output_buffer = io.StringIO()
                    sys.stdout = output_buffer
                    
                    try:
                        with open(result, 'r') as file:
                            exec(file.read(), {}, {})
                    except Exception as e:
                        print(f"Error: {str(e)}")
                    finally:
                        # Restore stdout and get output
                        sys.stdout = old_stdout
                        output = output_buffer.getvalue()
                        terminal.output_queue.put(output)
                
                # Run the script in a separate thread
                Thread(target=run_script, daemon=True).start()
        elif file_type == "pya":
            app_code = self.app_manager.execute_file(filename)
            if isinstance(app_code, str):  # If we got the app code
                app_window = PyAppWindow(f"PyOS App - {filename}", 100, 100, 800, 600, 
                                      app_code, self.window_manager)
                self.window_manager.create_window(app_window)
        else:
            content = self.app_manager.get_file_content(filename)
            if content:
                window = TextEditorWindow(filename, 100, 100, 400, 300, content, 
                                        self.app_manager.filesystem, filename)
                self.window_manager.create_window(window)

    def draw(self):
        # Draw icons
        for icon in self.icons:
            icon.draw(self.window_manager.screen)
            
        # Update taskbar window buttons
        self.taskbar.update_window_buttons(self.window_manager.windows)
        
        # Draw taskbar
        self.taskbar.draw(self.window_manager.screen)