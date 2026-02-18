from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

# --- Request/Result ---
class ToolRequest(BaseModel):
    tool_name: str
    action: str
    params: Dict[str, Any]
    requester_agent: str

class ToolResult(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None
    executed_at: str = Field(default="now") # ISO timestamp

# --- Router ---
class ToolRouter:
    def __init__(self):
        self.registry: Dict[str, Callable[[ToolRequest], ToolResult]] = {}
        # Register defaults
        self.register_tool("filesystem", self._handle_filesystem)
        self.register_tool("search", self._handle_search)

    def register_tool(self, name: str, handler: Callable):
        self.registry[name] = handler

    def route(self, request: ToolRequest) -> ToolResult:
        handler = self.registry.get(request.tool_name)
        if not handler:
            return ToolResult(success=False, data=None, error=f"Tool {request.tool_name} not found.")
        
        try:
            return handler(request)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # --- Built-in Tools ---
    def _handle_filesystem(self, req: ToolRequest) -> ToolResult:
        action = req.action
        path = req.params.get("path")
        content = req.params.get("content")
        
        if action == "write":
            # Stub local write
            if not path or not content:
                return ToolResult(success=False, data=None, error="Missing path or content")
            # In real system: os.write
            return ToolResult(success=True, data=f"Written {len(content)} bytes to {path}")
        
        elif action == "read":
            # Stub read
            return ToolResult(success=True, data=f"Content of {path}")
            
        return ToolResult(success=False, data=None, error="Action not supported")

    def _handle_search(self, req: ToolRequest) -> ToolResult:
        query = req.params.get("query")
        # Stub search response
        return ToolResult(
            success=True, 
            data=[{"title": f"Result for {query}", "link": "http://example.com"}]
        )
