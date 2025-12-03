import sys

sys.path.append("/tmp")
from windsurf_capsule_monitor import WindsurfIntegrationManager

manager = WindsurfIntegrationManager()

# After each Windsurf conversation, run:
manager.capture_windsurf_interaction(
    user_input="Your question to Windsurf",
    assistant_response="Windsurf's response",
    interaction_type="code_completion",  # or "debugging", "refactoring", etc.
    file_context="src/components/MyComponent.jsx",
    project_context="my-react-app",
)
