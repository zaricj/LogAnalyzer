"""Legacy signal connector.

New worker wiring now happens directly inside event handlers.
This module remains as a compatibility placeholder.
"""


class SignalConnector:
    """Compatibility shim kept during refactor."""

    def __init__(self, main_window):
        self.main_window = main_window
