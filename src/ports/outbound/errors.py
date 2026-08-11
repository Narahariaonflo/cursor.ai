"""Provider-independent outbound operation failures."""


class OutboundOperationError(Exception):
    """Classified adapter failure safe for orchestration decisions."""

    def __init__(self, code: str, retryable: bool) -> None:
        """Store a safe machine code and retry classification."""
        super().__init__(code)
        self.code = code
        self.retryable = retryable
