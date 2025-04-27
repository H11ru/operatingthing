# PyOS App API Documentation

## Overview
The PyOS App API provides a stable interface for apps to interact with the OS simulation. It exposes only the necessary methods and properties, ensuring compatibility and security.

## API Version
The current API version is **1.0**.

## Available Methods and Properties

### `windows`
- **Type**: Property
- **Description**: Returns a list of all open windows.

### `get_performance()`
- **Type**: Method
- **Description**: Returns system performance metrics, including CPU usage, memory usage, window count, and FPS.
- **Returns**: A dictionary with the following keys:
  - `cpu`: CPU usage percentage.
  - `memory`: Memory usage percentage.
  - `window_count`: Number of open windows.
  - `fps`: Current FPS.

### `terminate_window(window, caller_window=None)`
- **Type**: Method
- **Description**: Terminates a window. If `caller_window` is provided, it checks if the caller is the Task Manager.
- **Parameters**:
  - `window`: The window to terminate.
  - `caller_window`: The window calling the method (optional).
- **Returns**: `True` if the window was terminated, `False` otherwise.

### `filesystem`
- **Type**: Property
- **Description**: Returns the filesystem instance, allowing apps to interact with the virtual filesystem.

## Example Usage
```python
# Access the list of open windows
windows = api.windows

# Get system performance metrics
metrics = api.get_performance()
print(f"CPU: {metrics['cpu']}%, Memory: {metrics['memory']}%, FPS: {metrics['fps']}")

# Terminate a window
api.terminate_window(window)

# Access the filesystem
filesystem = api.filesystem
```

## Notes
- The API is designed to be stable and versioned. Apps can check `api.version` for compatibility.
- Only the documented methods and properties should be used to ensure compatibility. 