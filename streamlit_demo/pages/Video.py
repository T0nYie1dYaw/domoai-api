import asyncio
from typing import Optional

import httpx
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.models import VideoModel, get_v2v_model_info_by_instructions
from app.schema import VideoLength, VideoReferMode, Mode, VideoKey
from streamlit_demo.auth import check_password
from streamlit_demo.utils import polling_check_state, BASE_URL, BASE_HEADERS

if not check_password():
    st.stop()

st.title("Video")


async def run_video(prompt, refer_mode, model, length, video: UploadedFile, mode,
                    video_key, subject_only,
                    lip_sync, image: Optional[UploadedFile] = None):
    async with httpx.AsyncClient(base_url=BASE_URL, headers=BASE_HEADERS) as client:
        files = {'video': (video.name, video.read(), video.type)}
        if image:
            files['image'] = (image.name, image.read(), image.type)
        response = await client.post('/v1/video', data={
            "prompt": prompt,
            "refer_mode": refer_mode,
            "model": model,
            "length": length,
            "mode": mode if mode != 'auto' else None,
            "video_key": video_key if video_key != 'None' and subject_only is not True else None,
            "subject_only": subject_only,
            "lip_sync": lip_sync,
        }, files=files, timeout=30)
        if not response.is_success:
            st.error(f"Generate Fail: {response}")
            return None

    task_id = response.json().get('task_id', None)
    if task_id is None:
        return False, response.json()

    result = await polling_check_state(task_id=task_id)
    return True, result['videos'][0]['proxy_url']


mode = st.radio(label="Mode(*)", options=['auto'] + list(map(lambda x: x.value, Mode)), horizontal=True)

length = st.radio(label="Length(*)", options=list(map(lambda x: x.value, VideoLength)), horizontal=True)

video_models_value = list(map(lambda x: x.value, VideoModel))

model = st.selectbox(label="Model(*)", options=video_models_value,
                     index=video_models_value.index(VideoModel.ANIME_V1.value))

model_info = get_v2v_model_info_by_instructions(model)

refer_mode = st.radio(label="Refer Mode(*)",
                      options=list(map(lambda x: x.value, filter(lambda x: x in model_info.allowed_refer_modes,
                                                                 list(VideoReferMode)))),
                      horizontal=True)

lip_sync = st.checkbox(label="Lip Sync", key='lips', disabled=model_info.allowed_lip_sync is False)

subject_only = st.checkbox(label="Subject Only", key='so')

video_key = st.selectbox(label="Video Key", options=['None'] + list(map(lambda x: x.value, VideoKey)),
                         disabled=subject_only)

prompt = st.text_area(label="Prompt(*)")

video = st.file_uploader(label="Source Video(*)", type=['mp4'])

image = None
if model_info.allowed_reference_image:
    image = st.file_uploader(label="Source Image(*)", type=['jpg', 'jpeg', 'png'])

submitted = st.button("Submit")

if submitted:
    source_col, result_col = st.columns(2)
    with source_col:
        st.text("Source Video")
        if video:
            st.video(video)
    with source_col:
        st.text("Source Image")
        if image:
            st.image(image)

    with result_col:
        st.text("Result Video")
        result_video = st.empty()

    with result_col:
        with st.spinner('Wait for completion...'):
            # asyncio.run(asyncio.sleep(5))
            # result_video.video(video)
            status, result = asyncio.run(
                run_video(
                    prompt=prompt, refer_mode=refer_mode, model=model, length=length, video=video, mode=mode,
                    video_key=video_key, subject_only=subject_only, lip_sync=lip_sync, image=image,
                )
            )
            if not status:
                st.text(result)

            if status and result:
                result_video.video(result)
    st.success('Done!')
