import asyncio

import httpx


async def polling_check_state(task_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(f'http://127.0.0.1:8000/v1/task-data/{task_id}')
                response_json = response.json()
                if response_json['status'] == 'SUCCESS':
                    return response_json
            except Exception as e:
                pass
            await asyncio.sleep(1)
