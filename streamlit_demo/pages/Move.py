import asyncio

import httpx
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.schema import VideoLength, MoveModel, Mode
from streamlit_demo.auth import check_password
from streamlit_demo.utils import polling_check_state, BASE_URL

if not check_password():
    st.stop()

st.title("Move")


async def run_move(prompt, model, length, video: UploadedFile, image: UploadedFile, mode):
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post('/v1/move', data={
            "prompt": prompt,
            "model": model,
            "length": length,
            "mode": mode if mode != 'auto' else None
        }, files={'video': (video.name, video.read(), video.type), 'image': (image.name, image.read(), image.type)},
                                     timeout=30)
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return result['videos'][0]['proxy_url']


with st.form("move_form", border=True):
    mode = st.radio(label="Mode", options=['auto'] + list(map(lambda x: x.value, Mode)), horizontal=True)

    length = st.radio(label="Length", options=list(map(lambda x: x.value, VideoLength)), horizontal=True)

    model = st.selectbox(label="Model", options=list(map(lambda x: x.value, MoveModel)))

    prompt = st.text_area(label="Prompt")

    image = st.file_uploader(label="Source Image", type=['jpg', 'png'])
    video = st.file_uploader(label="Source Video", type=['mp4'])

    submitted = st.form_submit_button("Submit")

if submitted:
    source_image_col, source_video_col, result_col = st.columns(3)
    with source_image_col:
        st.text("Source Image")
        if image:
            st.image(image)

    with source_video_col:
        st.text("Source Video")
        if video:
            st.video(video)

    with result_col:
        st.text("Result Video")
        result_video = st.empty()

    with result_col:
        with st.spinner('Wait for completion...'):
            # asyncio.run(asyncio.sleep(5))
            # result_video.video(video)
            video_url = asyncio.run(
                run_move(prompt=prompt, model=model, length=length, video=video, image=image, mode=mode))
            if video_url:
                result_video.video(video_url)
    st.success('Done!')
