class AppManager:
    def __init__(self, filesystem):
        self.filesystem = filesystem

    def list_files(self):
        """List all files in the root directory"""
        try:
            contents = self.filesystem.list_directory()
            files = []
            for filename in contents["files"]:
                file = self.filesystem.read_file(filename)
                files.append((filename, file.file_type))
            return files
        except FileNotFoundError:
            return []

    def get_file_content(self, filename):
        """Get the content of a file"""
        try:
            file = self.filesystem.read_file(filename)
            return file.content
        except FileNotFoundError:
            return None

    def execute_file(self, filename):
        """Execute a file if it's executable"""
        try:
            return self.filesystem.execute_file(filename)
        except FileNotFoundError:
            return False

    def create_sample_files(self):
        """Create some sample files in the filesystem"""
        return # disabled.
    
        # Create a text file
        self.filesystem.create_file(
            "welcome.txt",
            "Welcome to PyOS!\n\nThis is a simple operating system simulation.",
            "txt"
        )

        # Create a sample PyOS application
        hello_app = """
import pygame

def main(screen):
    running = True
    font = pygame.font.Font(None, 36)
    text = font.render('Hello from PyOS App!', True, (0, 0, 0))
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        screen.fill((255, 255, 255))
        screen.blit(text, (10, 10))
        pygame.display.flip()
"""
        self.filesystem.create_file("hello.pya", hello_app, "pya")