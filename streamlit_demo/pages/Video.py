import asyncio

import httpx
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.schema import VideoLength, VideoReferMode, VideoModel, Mode
from streamlit_demo.utils import polling_check_state

st.title("Video")


async def run_video(prompt, refer_mode, model, length, video: UploadedFile, mode):
    async with httpx.AsyncClient() as client:
        response = await client.post('http://127.0.0.1:8000/v1/video', data={
            "prompt": prompt,
            "refer_mode": refer_mode,
            "model": model,
            "length": length,
            "mode": mode if mode != 'auto' else None
        }, files={'video': (video.name, video.read(), video.type)}, timeout=30)
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return result['videos'][0]['proxy_url']


with st.form("video_form", border=True):
    mode = st.radio(label="Mode", options=['auto'] + list(map(lambda x: x.value, Mode)), horizontal=True)

    length = st.radio(label="Length", options=list(map(lambda x: x.value, VideoLength)), horizontal=True)

    refer_mode = st.radio(label="Refer Mode", options=list(map(lambda x: x.value, VideoReferMode)), horizontal=True)

    model = st.selectbox(label="Model", options=list(map(lambda x: x.value, VideoModel)))

    prompt = st.text_area(label="Prompt")

    video = st.file_uploader(label="Source Video", type=['mp4'])

    submitted = st.form_submit_button("Submit")

if submitted:
    source_col, result_col = st.columns(2)
    with source_col:
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
            video_url = asyncio.run(run_video(prompt=prompt, refer_mode=refer_mode, model=model, length=length, video=video, mode=mode))
            if video_url:
                result_video.video(video_url)
    st.success('Done!')
