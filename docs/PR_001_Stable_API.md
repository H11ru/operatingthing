# PR: Refactor App API: Stable Interface for Task Manager and Apps

## Problem
The Task Manager app (`filesystem/tskmngr.pya`) is tightly coupled to the internal implementation of `WindowManager`. When the internal structure or method names of `WindowManager` change, the Task Manager app breaks. This is because the API is currently passed as the actual `WindowManager` instance, not a stable, versioned, or limited interface.

## Solution
Introduce a stable, versioned API layer for all PyOS apps, decoupling them from the internal implementation of `WindowManager`.

### Changes
1. **Add `PyOSAppAPI` Class**:
   - Create a dedicated API object for apps, exposing only the necessary methods and properties.
   - Do not pass the raw `WindowManager` instance to apps.
   - Version the API so future changes can be managed gracefully.

   Example:
   ```python
   class PyOSAppAPI:
       def __init__(self, window_manager, filesystem):
           self._wm = window_manager
           self._fs = filesystem

       @property
       def windows(self):
           return self._wm.windows

       def get_performance(self):
           return self._wm.get_performance()

       def terminate_window(self, window, caller_window=None):
           return self._wm.terminate_window(window, caller_window)

       @property
       def filesystem(self):
           return self._fs

       # Add more methods as needed, but keep the interface minimal and stable
   ```

2. **Update App Launching**:
   - In `PyAppWindow`, inject an instance of `PyOSAppAPI` as `api` in the app namespace.

3. **Update Task Manager App**:
   - Ensure `tskmngr.pya` only uses the documented API methods/properties.

4. **Add API Versioning**:
   - Add a version property to the API:
     ```python
     self.version = "1.0"
     ```
   - Apps can check `api.version` for compatibility.

5. **Document the API**:
   - Add a markdown file (e.g., `docs/app_api.md`) describing the available API for app developers.

6. **Add Tests**:
   - Add tests to ensure the API remains stable and that the Task Manager app works after changes.

## Benefits
- **Decoupling**: Apps are no longer tightly coupled to the internal implementation of `WindowManager`.
- **Stability**: The API is stable and versioned, preventing accidental breakage.
- **Security**: Exposing only the necessary methods and properties improves security and encapsulation.
- **Maintainability**: Easier to maintain and extend the API in the future.

## Testing
- Ensure the Task Manager app works after the changes.
- Add tests to verify the API remains stable.

## Documentation
- Update the README.md to reflect the changes.
- Add a new markdown file (`docs/app_api.md`) to document the API.

## Next Steps
- Implement the changes.
- Test the changes.
- Update the documentation.
- Submit the PR. 