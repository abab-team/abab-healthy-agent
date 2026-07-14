"""Official LangGraph SQLite checkpointer wiring."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from langgraph.checkpoint.sqlite import SqliteSaver


_THREAD_LOCKS: dict[tuple[Path, str], threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


class PersistentConversationCheckpointer:
    """Own a long-lived official ``SqliteSaver`` and its SQLite connection."""

    def __init__(self, checkpoint_path: str | Path) -> None:
        self.path = Path(checkpoint_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path), check_same_thread=False, timeout=5)
        self._connection.execute("PRAGMA busy_timeout = 5000")
        self.saver = SqliteSaver(self._connection)
        self.saver.setup()
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    @contextmanager
    def lock_thread(self, thread_id: str) -> Iterator[None]:
        """Serialize same-thread mutations in this process.

        SQLite remains the durable cross-process store. This explicit lock
        prevents two local requests from racing to append to the same
        ``configurable.thread_id`` and producing an ambiguous order.
        """

        key = (self.path, thread_id)
        with _THREAD_LOCKS_GUARD:
            lock = _THREAD_LOCKS.setdefault(key, threading.RLock())
        with lock:
            yield


_CHECKPOINTS: dict[Path, PersistentConversationCheckpointer] = {}


def get_persistent_checkpointer(checkpoint_path: str | Path) -> PersistentConversationCheckpointer:
    """Reuse one official saver per process; SQLite files persist across restarts."""

    path = Path(checkpoint_path).expanduser().resolve()
    checkpointer = _CHECKPOINTS.get(path)
    if checkpointer is None:
        checkpointer = PersistentConversationCheckpointer(path)
        _CHECKPOINTS[path] = checkpointer
    return checkpointer
