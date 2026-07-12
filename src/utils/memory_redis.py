from __future__ import annotations


class MemoryRedis:
    """In-memory Redis substitute for local development without Docker."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool | None:
        del ex  # TTL not needed for local dev
        if nx and key in self._data:
            return None
        self._data[key] = value
        return True

    async def close(self) -> None:
        self._data.clear()
