import asyncio

import httpx
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.models import VideoModel
from app.schema import VideoLength, VideoReferMode, Mode, VideoKey
from streamlit_demo.auth import check_password
from streamlit_demo.utils import polling_check_state, BASE_URL, BASE_HEADERS

if not check_password():
    st.stop()

st.title("Video")


async def run_video(prompt, refer_mode, model, length, video: UploadedFile, mode, video_key, subject_only,
                    lip_sync):
    async with httpx.AsyncClient(base_url=BASE_URL, headers=BASE_HEADERS) as client:
        response = await client.post('/v1/video', data={
            "prompt": prompt,
            "refer_mode": refer_mode,
            "model": model,
            "length": length,
            "mode": mode if mode != 'auto' else None,
            "video_key": video_key if video_key != 'None' else None,
            "subject_only": subject_only,
            "lip_sync": lip_sync,
        }, files={'video': (video.name, video.read(), video.type)}, timeout=30)
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json()['task_id']

    result = await polling_check_state(task_id=task_id)
    return result['videos'][0]['proxy_url']


with st.form("video_form", border=True):
    mode = st.radio(label="Mode(*)", options=['auto'] + list(map(lambda x: x.value, Mode)), horizontal=True)

    length = st.radio(label="Length(*)", options=list(map(lambda x: x.value, VideoLength)), horizontal=True)

    refer_mode = st.radio(label="Refer Mode(*)", options=list(map(lambda x: x.value, VideoReferMode)), horizontal=True)

    video_key = st.radio(label="Video Key", options=['None'] + list(map(lambda x: x.value, VideoKey)),
                         horizontal=True)

    subject_only = st.checkbox(label="Subject Only", key='so')

    lip_sync = st.checkbox(label="Lip Sync", key='lips')

    video_models_value = list(map(lambda x: x.value, VideoModel))

    model = st.selectbox(label="Model(*)", options=video_models_value,
                         index=video_models_value.index(VideoModel.ANIME_V1.value))

    prompt = st.text_area(label="Prompt(*)")

    video = st.file_uploader(label="Source Video(*)", type=['mp4'])

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
            video_url = asyncio.run(
                run_video(
                    prompt=prompt, refer_mode=refer_mode, model=model, length=length, video=video, mode=mode,
                    video_key=video_key, subject_only=subject_only, lip_sync=lip_sync
                )
            )
            if video_url:
                result_video.video(video_url)
    st.success('Done!')
