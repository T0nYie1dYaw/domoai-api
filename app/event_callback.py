import enum
from typing import Optional

import httpx
from tenacity import retry, wait_fixed, stop_after_attempt

from app.schema import TaskCacheData, TaskStateOut


class EventType(enum.Enum):
    TASK_SUCCESS = "TASK_SUCCESS"


class EventCallback:

    def __init__(self, callback_url: Optional[str]):
        self.callback_url = callback_url

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=False)
    async def send_task_success(self, task_id: str, data: TaskCacheData):
        if not self.callback_url:
            return
        out = TaskStateOut.from_cache_data(data)
        async with httpx.AsyncClient() as client:
            await client.post(self.callback_url, json={
                'event': EventType.TASK_SUCCESS.value,
                'task_id': task_id,
                'data': out.model_dump_json()
            })
