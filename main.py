import pygame
import os
from pathlib import Path
from system.window_manager import WindowManager
from system.filesystem import FileSystem
from system.desktop import Desktop
from system.app_manager import AppManager
from system.theme import current_theme

class PyOS:
    def __init__(self):
        pygame.init()
        
        # Set fullscreen mode
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        # Initialize clipboard support after setting display mode
        pygame.scrap.init()
        
        pygame.display.set_caption("PyOS")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize core systems
        self.filesystem = FileSystem()
        self.window_manager = WindowManager(self.screen)
        self.app_manager = AppManager(self.filesystem)
        
        # Create sample files first
        self.app_manager.create_sample_files()
        
        # Initialize desktop last, after files are created
        self.desktop = Desktop(self.window_manager, self.app_manager)
        
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F5:
                        # Refresh desktop icons when F5 is pressed
                        self.desktop.refresh_icons()
                    
                self.desktop.handle_event(event)
                self.window_manager.handle_event(event)  # Let window manager handle all keyboard events
            
            # Update
            self.window_manager.update()
            
            # Draw
            self.screen.fill(current_theme.background)  # Use theme background
            self.desktop.draw()
            self.window_manager.draw()
            pygame.display.flip()
            
            self.clock.tick(60)
        self.screen.fill((0, 0, 0))  # Clear screen before quitting
        pygame.display.flip()
        pygame.time.delay(1300)
        self.screen.fill((255, 255, 255))  # Clear screen before quitting
        pygame.display.flip()
        pygame.time.delay(74)
        self.screen.fill((0,0,0))  # Clear screen before quitting
        pygame.display.flip()
        pygame.time.delay(474)
        for i in range(15):
            self.screen.fill((255, 255, 255))  # Clear screen before quitting
            pygame.display.flip()
            pygame.time.delay(6)
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
            pygame.time.delay(6)
        self.screen.fill((0,0,0))
        pygame.display.flip()
        pygame.time.delay(300)
        pygame.quit()

if __name__ == "__main__":
    os = PyOS()
    os.run()