import os
import abc
import logging
from typing import Dict, Any, Optional, List
from src.shared.logger import AgentLogger

# Configure basic logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Integration(abc.ABC):
    """
    Abstract Base Class for all external integrations.
    """
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_connected = False

    @abc.abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the external service.
        Returns True if successful, False otherwise.
        """
        pass

    @abc.abstractmethod
    def disconnect(self):
        """
        Close the connection and cleanup resources.
        """
        pass

    @abc.abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """
        Execute a specific action on the integration.
        """
        pass

    @abc.abstractmethod
    def health_check(self) -> bool:
        """
        Check if the integration is healthy.
        """
        pass

class IntegratorAgent:
    """
    The Integrator Agent: Centralized manager for all external API connections.
    """
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.agent_logger = AgentLogger(project_id)
        self.registry: Dict[str, Integration] = {}

    def register_integration(self, integration: Integration):
        """
        Registers a new integration with the agent.
        """
        logger.info(f"Registering integration: {integration.name}")
        self.registry[integration.name] = integration

    def connect_all(self):
        """
        Attempts to connect all registered integrations.
        """
        results = {}
        for name, integration in self.registry.items():
            try:
                success = integration.connect()
                integration.is_connected = success
                status = "Connected" if success else "Failed"
                results[name] = status
                self.agent_logger.log("Integrator", f"Connection to {name}: {status}")
            except Exception as e:
                logger.error(f"Failed to connect to {name}: {e}")
                results[name] = f"Error: {str(e)}"
                self.agent_logger.log("Integrator", f"Connection to {name} failed: {e}", severity="ERROR")
        return results

    def execute(self, integration_name: str, action: str, params: Dict[str, Any] = {}) -> Any:
        """
        Routes an execution request to the specified integration.
        """
        integration = self.registry.get(integration_name)
        if not integration:
            error_msg = f"Integration '{integration_name}' not found."
            self.agent_logger.log("Integrator", error_msg, severity="ERROR")
            raise ValueError(error_msg)

        if not integration.is_connected:
             self.agent_logger.log("Integrator", f"Attempting lazy connection required for {integration_name}")
             if not integration.connect():
                 raise ConnectionError(f"Could not connect to {integration_name}")
        
        try:
            self.agent_logger.log("Integrator", f"Executing {action} on {integration_name}")
            result = integration.execute(action, params)
            # Todo: Calculate and log usage cost if applicable
            return result
        except Exception as e:
            self.agent_logger.log("Integrator", f"Action {action} on {integration_name} failed: {e}", severity="ERROR")
            raise e
        
class MockIntegration(Integration):
    """
    A mock integration for testing purposes.
    """
    def connect(self) -> bool:
        return True

    def disconnect(self):
        pass

    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "echo":
            return params
        return "Unknown action"

    def health_check(self) -> bool:
        return True

# --- Google Integrations ---

class GeminiIntegration(Integration):
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.client: Optional[Any] = None
        self.model_name: str = config.get("model", "gemini-2.0-flash")

    def connect(self) -> bool:
        try:
            from google import genai
            api_key = self.config.get("api_key") or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.error("Gemini API Key not found.")
                return False
            self.client = genai.Client(api_key=api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            return False

    def disconnect(self):
        self.client = None

    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        if not self.is_connected or not self.client:
            raise ConnectionError("Gemini not connected")
        
        if action == "generate_content":
            prompt = params.get("prompt")
            if not prompt:
                raise ValueError("Prompt is required")
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}")
                raise e
        return None

    def health_check(self) -> bool:
        return self.is_connected and self.client is not None

class DriveIntegration(Integration):
    def connect(self) -> bool:
        # Placeholder for actual OAuth flow / Service Account auth
        # In a real scenario, this would load credentials
        logger.info("Initializing Drive Service...")
        return True

    def disconnect(self):
        pass

    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "upload_file":
            logger.info(f"Uploading file: {params.get('name')}")
            # Mocking upload for now to avoid complexity without real creds
            return {"id": "mock_drive_file_id", "name": params.get("name")}
        return None

    def health_check(self) -> bool:
        return True

class GmailIntegration(Integration):
    def connect(self) -> bool:
        logger.info("Initializing Gmail Service...")
        return True

    def disconnect(self):
        pass

    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "send_email":
            logger.info(f"Sending email to {params.get('to')}")
            return {"status": "sent", "id": "mock_msg_id"}
        return None
    
    def health_check(self) -> bool:
        return True

class CalendarIntegration(Integration):
    def connect(self) -> bool:
        logger.info("Initializing Calendar Service...")
        return True

    def disconnect(self):
        pass
    
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "create_event":
            logger.info(f"Creating event: {params.get('summary')}")
            return {"status": "created", "id": "mock_event_id"}
        return None

    def health_check(self) -> bool:
        return True
