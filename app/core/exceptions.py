class SpendTalkException(Exception):
    """Base exception for SpendTalk errors."""
    pass

class AuthError(SpendTalkException):
    """Exception raised for authentication or authorization failures."""
    def __init__(self, message: str = "Invalid credentials"):
        self.message = message
        super().__init__(self.message)

class ResourceNotFoundError(SpendTalkException):
    """Exception raised when a resource is not found."""
    def __init__(self, resource: str, identifier: str):
        self.message = f"{resource} identified by {identifier} was not found"
        super().__init__(self.message)

class APIConnectionError(SpendTalkException):
    """Exception raised when Gemini API or database connection fails."""
    def __init__(self, service: str, detail: str):
        self.message = f"Failed to connect to {service}: {detail}"
        super().__init__(self.message)
