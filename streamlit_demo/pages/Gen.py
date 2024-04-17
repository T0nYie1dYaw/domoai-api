import asyncio

import httpx
import streamlit as st

from streamlit_demo.utils import polling_check_state

st.title("Gen")


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
    return result['images'][0]['proxy_url']


with st.form("gen_form", border=False):
    prompt = st.text_input(label="Prompt")
    image = st.file_uploader(label="Reference Image", type=['jpg', 'png'])
    submitted = st.form_submit_button("Submit")

if submitted:
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
            image_url = asyncio.run(gen(prompt, image))
            result_image.image(image_url)
    st.success('Done!')
