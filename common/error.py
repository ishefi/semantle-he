class HSError(Exception):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"Error: {self.message} ({self.code})"
