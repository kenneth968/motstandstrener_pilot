"""Performance profiler for tracking execution time of various components."""

import time
import contextlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ProfileEntry:
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, str] = field(default_factory=dict)

class Profiler:
    """Simple profiler to track execution times."""

    def __init__(self):
        self._entries: List[ProfileEntry] = []
        self._active: Dict[str, ProfileEntry] = {}

    @contextlib.contextmanager
    def profile(self, name: str, **metadata):
        """Context manager for profiling a block of code."""
        entry = self.start(name, **metadata)
        try:
            yield entry
        finally:
            self.stop(name)

    def start(self, name: str, **metadata) -> ProfileEntry:
        """Start profiling a named operation."""
        # If the same name is already active, we might want to handle it (recursion/nesting)
        # For simplicity, we'll just overwrite or ignore nesting for now, 
        # but let's append a unique suffix if needed or just trust the user.
        # Actually, let's just create a new entry.
        entry = ProfileEntry(name=name, start_time=time.time(), metadata=metadata)
        self._active[name] = entry
        self._entries.append(entry)
        return entry

    def stop(self, name: str) -> None:
        """Stop profiling a named operation."""
        if name in self._active:
            entry = self._active[name]
            entry.end_time = time.time()
            entry.duration = entry.end_time - entry.start_time
            del self._active[name]

    def get_entries(self) -> List[ProfileEntry]:
        """Return all recorded entries."""
        return self._entries

    def clear(self) -> None:
        """Clear all entries."""
        self._entries = []
        self._active = {}
