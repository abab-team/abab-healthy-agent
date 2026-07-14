"""Official LangGraph SQLite checkpointer wiring."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


class PersistentConversationCheckpointer:
    """Own a long-lived official ``SqliteSaver`` and its SQLite connection."""

    def __init__(self, checkpoint_path: str | Path) -> None:
        self.path = Path(checkpoint_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self.saver = SqliteSaver(self._connection)
        self.saver.setup()

    def close(self) -> None:
        self._connection.close()


_CHECKPOINTS: dict[Path, PersistentConversationCheckpointer] = {}


def get_persistent_checkpointer(checkpoint_path: str | Path) -> PersistentConversationCheckpointer:
    """Reuse one official saver per process; SQLite files persist across restarts."""

    path = Path(checkpoint_path).expanduser().resolve()
    checkpointer = _CHECKPOINTS.get(path)
    if checkpointer is None:
        checkpointer = PersistentConversationCheckpointer(path)
        _CHECKPOINTS[path] = checkpointer
    return checkpointer
