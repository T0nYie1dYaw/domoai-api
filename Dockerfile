FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

ENV PYTHONUNBUFFERED 1

ENV DISCORD_TOKEN ''
ENV DISCORD_GUILD_ID ''
ENV DISCORD_CHANNEL_ID ''

ENV EVENT_CALLBACK_URL ''

ENV AUTH_TOKEN ''

ENV REDIS_URI ''

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
