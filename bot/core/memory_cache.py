import time
import asyncio

class MemoryCache:
    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        data = self.store.get(key)
        if not data:
            return None
        
        val, expire_at = data
        if expire_at and time.time() > expire_at:
            del self.store[key]
            return None
        return val

    async def setex(self, key: str, time_seconds: int, value: str):
        expire_at = time.time() + time_seconds
        self.store[key] = (value, expire_at)

    async def set(self, key: str, value: str, ex: int = None):
        expire_at = (time.time() + ex) if ex else None
        self.store[key] = (value, expire_at)

    async def close(self):
        self.store.clear()
