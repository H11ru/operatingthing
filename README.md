# PyOS: A Simple Operating System Simulation in Pygame

## Overview
PyOS is a desktop/OS simulation built using Pygame. It mimics a basic operating system with a desktop, taskbar, window management, and a virtual filesystem. It supports running custom Python-based apps (`.pya` files) and provides a simple API for app developers.

## Features
- **Desktop Environment**: Fullscreen window with a taskbar, desktop icons, and windowed applications.
- **Window Management**: Open, move, and close windows, similar to a real OS.
- **Virtual Filesystem**: Create, read, and execute files from within the OS simulation.
- **App Support**: Run custom Python-based apps (`.pya` files) and open text files in a built-in editor.
- **Taskbar & Power Button**: Manage open windows and shut down the OS simulation.
- **Theme Support**: Customizable look and feel via a theme system.

## Setup
1. **Install Requirements**:
   ```sh
   pip install -r requirements.txt
   ```
2. **Run the OS**:
   ```sh
   python main.py
   ```

## Usage
- Use the desktop and taskbar to open files and apps.
- Use the shutdown button to exit.

## Project Structure
- `main.py`: Entry point, initializes core systems and runs the main event loop.
- `system/`: Core modules (window_manager, filesystem, desktop, app_manager, theme).
- `filesystem/`: Virtual filesystem and app files (`.pya`).

## Contributing
Feel free to submit PRs or issues to improve the demo!
