import asyncio
from typing import List

import httpx
import streamlit as st
from pydantic import BaseModel

from app.schema import Mode
from streamlit_demo.utils import polling_check_state, build_upscale_vary_buttons, BASE_URL

st.title("REAL")

if 'real_result' not in st.session_state:
    st.session_state.real_result = None

if 'uv_results' not in st.session_state:
    st.session_state.uv_results = []


class Result(BaseModel):
    task_id: str
    image_url: str
    upscale_indices: List[int]
    vary_indices: List[int]


async def real(prompt, image, mode):
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        if prompt:
            data = {
                "prompt": prompt,
                "mode": mode if mode != 'auto' else None
            }
        else:
            data = {
                "mode": mode if mode != 'auto' else None
            }
        response = await client.post(
            '/v1/real',
            data=data,
            files={'image': (image.name, image.read(), image.type)},
            timeout=30
        )
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return task_id, result['images'][0]['proxy_url'], result['upscale_indices'], result['vary_indices']


async def upscale(task_id, index):
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post('/v1/upscale', data={
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
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post('/v1/vary', data={
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
    mode = st.radio(label="Mode", options=['auto'] + list(map(lambda x: x.value, Mode)), horizontal=True)

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
    st.session_state.real_result = None

if submitted or st.session_state.real_result:
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
            if not st.session_state.real_result:
                st.session_state.real_result = asyncio.run(real(prompt, image, mode))
            task_id, image_url, upscale_indices, vary_indices = st.session_state.real_result
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
