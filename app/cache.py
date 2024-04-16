from __future__ import annotations

from typing import Any, Optional

from redis.asyncio import Redis, from_url

from app.schema import TaskCacheData


class Cache:
    def __init__(self, prefix: str = ''):
        self.prefix = prefix

    async def set_value(self, key: str, value: Any, ex: Optional[int] = None):
        pass

    async def get_value(self, key: str):
        pass

    async def close(self):
        pass

    @staticmethod
    def __get_message_id2task_id_key(message_id: str) -> str:
        return f'message_id2task_id:{message_id}'

    async def set_message_id2task_id(
            self,
            message_id: str,
            task_id: str
    ):
        await self.set_value(key=self.__get_message_id2task_id_key(message_id), value=task_id)

    async def get_task_id_by_message_id(self, message_id: str) -> Optional[str]:
        value = await self.get_value(key=self.__get_message_id2task_id_key(message_id))
        if value:
            try:
                return str(value)
            except Exception as e:
                # TODO:
                pass
        return None

    @staticmethod
    def __get_task_id2data_key(task_id: str) -> str:
        return f'task_id2data:{task_id}'

    async def set_task_id2data(
            self,
            task_id: str,
            data: TaskCacheData
    ):
        await self.set_value(key=self.__get_task_id2data_key(task_id), value=data.model_dump_json())

    async def get_task_data_by_id(self, task_id: str) -> Optional[TaskCacheData]:
        value = await self.get_value(key=self.__get_task_id2data_key(task_id))
        if value:
            try:
                return TaskCacheData.model_validate_json(value)
            except Exception as e:
                # TODO:
                pass
        return None


class MemoryCache(Cache):
    def __init__(self, prefix: str = ''):
        super().__init__(prefix=prefix)
        self.data = {}

    async def set_value(self, key: str, value: Any, ex: Optional[int] = None):
        self.data[f"{self.prefix}{key}"] = value

    async def get_value(self, key: str):
        return self.data.get(f"{self.prefix}{key}")


class RedisCache(Cache):
    def __init__(self, redis: Redis, prefix: str = ''):
        super().__init__(prefix=prefix)
        self.redis = redis

    async def set_value(self, key: str, value: Any, ex: Optional[int] = None):
        await self.redis.set(name=f"{self.prefix}{key}", value=value, ex=ex)

    async def get_value(self, key: str):
        return await self.redis.get(name=f"{self.prefix}{key}")

    async def close(self):
        await self.redis.close()

    @staticmethod
    async def init_redis_pool(redis_uri: str) -> Redis:
        redis = await from_url(
            redis_uri,
            encoding="utf-8",
            decode_responses=True,
        )
        return redis
