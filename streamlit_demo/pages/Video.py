import asyncio

import httpx
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.schema import VideoLength, VideoReferMode, VideoModel

st.title("Video")


async def run_video(prompt, refer_mode, model, length, video: UploadedFile):
    async with httpx.AsyncClient() as client:
        response = await client.post('http://127.0.0.1:8000/v1/video', data={
            "prompt": prompt,
            "refer_mode": refer_mode,
            "model": model,
            "length": length
        }, files={'video': video.read()}, timeout=30)
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json()['task_id']

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(f'http://127.0.0.1:8000/v1/task-data/{task_id}')
            response_json = response.json()
            if response_json['status'] == 'SUCCESS':
                video_url = response_json['videos'][0]['proxy_url']
                return video_url
            await asyncio.sleep(1)


with st.form("video_form", border=True):
    length = st.radio(label="Length", options=list(map(lambda x: x.value, VideoLength)), horizontal=True)

    refer_mode = st.radio(label="Refer Mode", options=list(map(lambda x: x.value, VideoReferMode)), horizontal=True)

    model = st.selectbox(label="Model", options=list(map(lambda x: x.value, VideoModel)))

    prompt = st.text_input(label="Prompt")

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
            video_url = asyncio.run(run_video(prompt=prompt, refer_mode=refer_mode, model=model, length=length, video=video))
            if video_url:
                result_video.video(video_url)
    st.success('Done!')
