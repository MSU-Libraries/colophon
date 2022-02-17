"""
Colophon global state functionality
"""
from dataclasses import dataclass
import app

@dataclass
class StateEntry:
    """Single state entry"""
    def __init__(self):
        self.associated = False

class State:
    """Global state of a Colophon run"""
    def __init__(self):
        self.entries = {}

    def add(self, filepath):
        """Create a new entry for the filepath"""
        if filepath in self.entries:
            raise app.ColophonException(f"Cannot add state entry for one that already exists: {filepath}")
        self.entries[filepath] = StateEntry()

    def __getitem__(self, filepath):
        return self.entries[filepath]

