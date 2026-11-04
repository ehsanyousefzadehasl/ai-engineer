
class ToolError(Exception):
    """Base class for tool-related failures."""


class ToolAuthorizationError(ToolError):
    pass


class ToolValidationError(ToolError):
    pass


class ToolExecutionError(ToolError):
    pass


class ToolTimeoutError(ToolError):
    pass
