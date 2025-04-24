class Theme:
    pass

class CyberTheme(Theme):
    def __init__(self):
        # Main colors
        self.background = (0, 0, 0)  # Black
        self.accent = (0, 255, 0)  # Bright green
        self.text = (0, 255, 0)  # Green text
        self.dim_text = (0, 180, 0)  # Dimmer green for secondary text
        
        # Window colors
        self.window_bg = (0, 0, 0)
        self.window_title_active = (0, 255, 0)
        self.window_title_inactive = (0, 50, 0)
        self.title_text = (0, 0, 0)  # Black text on title bar for contrast with green bar
        self.window_border_active = (0, 255, 0)
        self.window_border_inactive = (0, 50, 0)
        
        # Taskbar colors (more green)
        self.taskbar_bg = (0, 50, 0)
        self.taskbar_border = (0, 120, 0)
        self.taskbar_button = (0, 120, 0)
        self.taskbar_button_hover = (0, 180, 0)  # Lighter green when hovered
        
        # Button colors
        self.button_bg = (0, 50, 0)
        self.button_hover = (0, 120, 0)  # Darker green when hovered
        self.button_active = (0, 250, 0)  # Even darker green when active
        
        # Editor colors
        self.editor_bg = (0, 0, 0)  # Black
        self.editor_text = (0, 255, 0)  # Bright green
        self.editor_cursor = (0, 255, 0)  # Bright green
        self.editor_selection = (0, 80, 0)  # Dark green for selection
        
        # Terminal colors
        self.terminal_bg = (0, 0, 0)  # Black
        self.terminal_text = (0, 255, 0)  # Bright green
        
        # Desktop colors
        self.desktop_bg = (0, 230, 0)

        
# Global theme instance
current_theme = CyberTheme()