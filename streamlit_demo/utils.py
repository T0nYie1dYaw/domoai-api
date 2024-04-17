import asyncio
from typing import Optional

import httpx


async def polling_check_state(task_id: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(f'http://127.0.0.1:8000/v1/task-data/{task_id}')
            if response.status_code == 404:
                return None
            response_json = response.json()
            if response_json['status'] == 'SUCCESS':
                return response_json
            await asyncio.sleep(1)
