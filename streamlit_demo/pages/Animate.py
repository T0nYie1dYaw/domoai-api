import asyncio

import httpx
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.schema import AnimateLength, AnimateIntensity, Mode
from streamlit_demo.auth import check_password
from streamlit_demo.utils import polling_check_state, BASE_URL, BASE_HEADERS

if not check_password():
    st.stop()

st.title("Animate")


async def run_animate(prompt, intensity, length, image: UploadedFile, mode):
    async with httpx.AsyncClient(base_url=BASE_URL, headers=BASE_HEADERS) as client:
        response = await client.post('/v1/animate', data={
            "prompt": prompt,
            "intensity": intensity,
            "length": length,
            "mode": mode if mode != 'auto' else None
        }, files={'image': (image.name, image.read(), image.type)}, timeout=30)
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return result['videos'][0]['proxy_url']


with st.form("real_form", border=True):
    mode = st.radio(label="Mode(*)", options=['auto'] + list(map(lambda x: x.value, Mode)), horizontal=True)

    length = st.radio(label="Length(*)", options=list(map(lambda x: x.value, AnimateLength)), horizontal=True)

    intensity = st.radio(label="Intensity(*)", options=list(map(lambda x: x.value, AnimateIntensity)), horizontal=True)

    image = st.file_uploader(label="Source Image(*)", type=['jpg', 'png'])

    prompt = st.text_area(label="Prompt")

    submitted = st.form_submit_button("Submit")

if submitted:
    source_col, result_col = st.columns(2)
    with source_col:
        st.text("Source Image")
        if image:
            st.image(image)

    with result_col:
        st.text("Result Video")
        result_video = st.empty()

    with result_col:
        with st.spinner('Wait for completion...'):
            videos_url = asyncio.run(
                run_animate(prompt=prompt, intensity=intensity, length=length, image=image, mode=mode))
            if videos_url:
                result_video.video(videos_url)
    st.success('Done!')
