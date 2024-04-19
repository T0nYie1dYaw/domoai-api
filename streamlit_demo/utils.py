import asyncio
import os
from typing import Optional, List, Callable

import httpx
import streamlit as st
from pydantic import BaseModel

BASE_URL = os.environ.get('STREAMLIT_BASE_URL')

API_AUTH_TOKEN = os.environ.get('API_AUTH_TOKEN')

if not BASE_URL:
    BASE_URL = 'http://127.0.0.1:8000'

if API_AUTH_TOKEN:
    BASE_HEADERS = {
        'Authorization': f'Bearer {API_AUTH_TOKEN}'
    }
else:
    BASE_HEADERS = {

    }


async def polling_check_state(task_id: str) -> Optional[dict]:
    async with httpx.AsyncClient(base_url=BASE_URL, headers=BASE_HEADERS) as client:
        while True:
            response = await client.get(f'/v1/task-data/{task_id}')
            if response.status_code == 404:
                return None
            response_json = response.json()
            if response_json['status'] == 'SUCCESS':
                return response_json
            await asyncio.sleep(1)


def build_upscale_vary_buttons(
        task_id: str,
        upscale_indices: List[int],
        vary_indices: List[int],
        on_click_upscale: Callable[[str, int], None],
        on_click_vary: Callable[[str, int], None]
):
    upscale_container, vary_container = st.columns(2)
    upscale_cols_1, upscale_cols_2 = upscale_container.columns(2)
    upscale_cols_3, upscale_cols_4 = upscale_container.columns(2)
    upscale_cols_1.button(
        label=f":mag: U1",
        use_container_width=True,
        disabled=1 not in upscale_indices,
        on_click=on_click_upscale,
        args=(task_id, 1),
        key=f'U1-{task_id}'
    )
    upscale_cols_2.button(
        label=f":mag: U2",
        use_container_width=True,
        disabled=2 not in upscale_indices,
        on_click=on_click_upscale,
        args=(task_id, 2),
        key=f'U2-{task_id}'
    )
    upscale_cols_3.button(
        label=f":mag: U3",
        use_container_width=True,
        disabled=3 not in upscale_indices,
        on_click=on_click_upscale,
        args=(task_id, 3),
        key=f'U3-{task_id}'
    )
    upscale_cols_4.button(
        label=f":mag: U4",
        use_container_width=True,
        disabled=4 not in upscale_indices,
        on_click=on_click_upscale,
        args=(task_id, 4),
        key=f'U4-{task_id}'
    )

    vary_cols_1, vary_cols_2 = vary_container.columns(2)
    vary_cols_3, vary_cols_4 = vary_container.columns(2)
    vary_cols_1.button(
        label=f":magic_wand: V1",
        use_container_width=True,
        disabled=1 not in vary_indices,
        on_click=on_click_vary,
        args=(task_id, 1),
        key=f'V1-{task_id}'
    )
    vary_cols_2.button(
        label=f":magic_wand: V2",
        use_container_width=True,
        disabled=2 not in vary_indices,
        on_click=on_click_vary,
        args=(task_id, 2),
        key=f'V2-{task_id}'
    )
    vary_cols_3.button(
        label=f":magic_wand: V3",
        use_container_width=True,
        disabled=3 not in vary_indices,
        on_click=on_click_vary,
        args=(task_id, 3),
        key=f'V3-{task_id}'
    )
    vary_cols_4.button(
        label=f":magic_wand: V4",
        use_container_width=True,
        disabled=4 not in vary_indices,
        on_click=on_click_vary,
        args=(task_id, 4),
        key=f'V4-{task_id}'
    )


class UVResult(BaseModel):
    task_id: str
    image_url: str
    upscale_indices: List[int]
    vary_indices: List[int]
