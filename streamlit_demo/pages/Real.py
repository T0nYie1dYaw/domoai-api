import asyncio

import httpx
import streamlit as st

from app.schema import Mode
from streamlit_demo.auth import check_password
from streamlit_demo.utils import polling_check_state, build_upscale_vary_buttons, UVResult, BASE_URL, \
    BASE_HEADERS

if not check_password():
    st.stop()

st.title("REAL")

if 'real_result' not in st.session_state:
    st.session_state.real_result = None

if 'real_uv_results' not in st.session_state:
    st.session_state.real_uv_results = []


async def real(prompt, image, mode):
    async with httpx.AsyncClient(base_url=BASE_URL, headers=BASE_HEADERS) as client:
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
    async with httpx.AsyncClient(base_url=BASE_URL, headers=BASE_HEADERS) as client:
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
    async with httpx.AsyncClient(base_url=BASE_URL, headers=BASE_HEADERS) as client:
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


with st.form("real_form", border=False):
    mode = st.radio(label="Mode(*)", options=['auto'] + list(map(lambda x: x.value, Mode)), horizontal=True)
    image = st.file_uploader(label="Reference Image(*)", type=['jpg', 'png'])
    prompt = st.text_area(label="Prompt")
    submitted = st.form_submit_button("Submit")


def on_click_upscale(task_id: str, index: int):
    with st.spinner('Wait for completion...'):
        task_id, images_url, upscale_indices, vary_indices = asyncio.run(upscale(task_id=task_id, index=index))
    st.session_state.real_uv_results.append(UVResult(
        task_id=task_id,
        image_url=images_url,
        upscale_indices=upscale_indices,
        vary_indices=vary_indices
    ))


def on_click_vary(task_id: str, index: int):
    with st.spinner('Wait for completion...'):
        task_id, images_url, upscale_indices, vary_indices = asyncio.run(vary(task_id=task_id, index=index))
    st.session_state.real_uv_results.append(UVResult(
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

for item in st.session_state.real_uv_results:
    result: UVResult = item
    st.image(result.image_url)
    build_upscale_vary_buttons(
        task_id=result.task_id,
        upscale_indices=result.upscale_indices,
        vary_indices=result.vary_indices,
        on_click_upscale=on_click_upscale,
        on_click_vary=on_click_vary
    )
