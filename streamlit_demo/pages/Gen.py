import asyncio
from typing import List, Callable

import httpx
import streamlit as st
from pydantic import BaseModel

from streamlit_demo.utils import polling_check_state

st.title("Gen")

if 'gen_result' not in st.session_state:
    st.session_state.gen_result = None

if 'uv_results' not in st.session_state:
    st.session_state.uv_results = []


class Result(BaseModel):
    task_id: str
    image_url: str
    upscale_indices: List[int]
    vary_indices: List[int]


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


def build_vary_buttons(task_id: str, vary_indices: List[int]):
    if vary_indices:
        vary_cols = st.columns(len(vary_indices))
        for column_index, value in enumerate(vary_indices):
            vary_cols[column_index].button(label=f"V{value}", use_container_width=True, key=f'{task_id}:V{value}')


async def gen(prompt, image):
    async with httpx.AsyncClient() as client:
        response = await client.post('http://127.0.0.1:8000/v1/gen', data={
            "prompt": prompt
        }, files={'image': (image.name, image.read(), image.type)} if image else None, timeout=30)
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return task_id, result['images'][0]['proxy_url'], result['upscale_indices'], result['vary_indices']


async def upscale(task_id, index):
    async with httpx.AsyncClient() as client:
        response = await client.post('http://127.0.0.1:8000/v1/upscale', data={
            "task_id": task_id,
            "index": index
        }, timeout=30)
        if not response.is_success:
            st.error(f"Upscale Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return task_id, result['images'][0]['proxy_url'], result['upscale_indices'], result['vary_indices']


async def vary(task_id, index):
    async with httpx.AsyncClient() as client:
        response = await client.post('http://127.0.0.1:8000/v1/vary', data={
            "task_id": task_id,
            "index": index
        }, timeout=30)
        if not response.is_success:
            st.error(f"Vary Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return task_id, result['images'][0]['proxy_url'], result['upscale_indices'], result['vary_indices']


with st.form("gen_form", border=False):
    prompt = st.text_area(label="Prompt")
    image = st.file_uploader(label="Reference Image", type=['jpg', 'png'])
    submitted = st.form_submit_button("Submit")


def on_click_upscale(task_id: str, index: int):
    with st.spinner('Wait for completion...'):
        task_id, images_url, upscale_indices, vary_indices = asyncio.run(upscale(task_id=task_id, index=index))
    st.session_state.uv_results.append(Result(
        task_id=task_id,
        image_url=images_url,
        upscale_indices=upscale_indices,
        vary_indices=vary_indices
    ))


def on_click_vary(task_id: str, index: int):
    with st.spinner('Wait for completion...'):
        task_id, images_url, upscale_indices, vary_indices = asyncio.run(vary(task_id=task_id, index=index))
    st.session_state.uv_results.append(Result(
        task_id=task_id,
        image_url=images_url,
        upscale_indices=upscale_indices,
        vary_indices=vary_indices
    ))


if submitted:
    st.session_state.gen_result = None

if submitted or st.session_state.gen_result:
    if image:
        source_col, result_col = st.columns(2)
        with source_col:
            st.text("Reference")
            if image:
                st.image(image)
    else:
        result_col = st.container()

    with result_col:
        st.text("Result")
        result_image = st.empty()

    with result_col:
        with st.spinner('Wait for completion...'):
            if not st.session_state.gen_result:
                st.session_state.gen_result = asyncio.run(gen(prompt, image))
            task_id, image_url, upscale_indices, vary_indices = st.session_state.gen_result
            result_image.image(image_url)
    build_upscale_vary_buttons(
        task_id=task_id,
        upscale_indices=upscale_indices,
        vary_indices=vary_indices,
        on_click_upscale=on_click_upscale,
        on_click_vary=on_click_vary
    )

for item in st.session_state.uv_results:
    result: Result = item
    st.image(result.image_url)
    build_upscale_vary_buttons(
        task_id=result.task_id,
        upscale_indices=result.upscale_indices,
        vary_indices=result.vary_indices,
        on_click_upscale=on_click_upscale,
        on_click_vary=on_click_vary
    )

#
#     if st.session_state.upscale_result:
#         upscale_task_id, upscale_image_url, upscale_vary_indices = st.session_state.upscale_result
#
#         st.image(upscale_image_url)
#         build_vary_buttons(task_id=upscale_task_id, vary_indices=upscale_vary_indices)
