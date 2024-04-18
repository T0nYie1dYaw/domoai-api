FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./requirements-dev.txt /code/requirements-dev.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements-dev.txt

COPY ./app /code/app
COPY ./streamlit_demo /code/streamlit_demo

ENV PYTHONUNBUFFERED 1

ENV STREAMLIT_BASE_URL ''
ENV STREAMLIT_AUTH ''

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["python", "-m", "streamlit", "run", "/code/streamlit_demo/🏠_Home.py", "--server.port=8501", "--server.address=0.0.0.0"]