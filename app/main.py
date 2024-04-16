import asyncio
import io
import uuid
from typing import Optional

import discord
from fastapi import FastAPI, Request, UploadFile, Form, HTTPException
from starlette import status

from app.cache import RedisCache, MemoryCache, Cache
from app.schema import VideoModel, VideoReferMode, VideoLength, TaskCacheData, TaskStatus
from app.settings import get_settings
from app.user_client import DiscordUserClient

app = FastAPI()

settings = get_settings()


@app.post("/v1/gen")
async def gen_api(
        request: Request,
        image: Optional[UploadFile] = None,
        prompt: str = Form(...)
):
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client
    if image:
        image_bytes = await image.read()
    else:
        image_bytes = None
    interaction = await discord_user_client.gen(prompt=prompt, image=io.BytesIO(image_bytes) if image_bytes else None)
    print(f"gen, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    message: discord.Message = await discord_user_client.wait_for(
        'message',
        check=lambda m: m.embeds and ('Waiting to start' in m.embeds[0].description),
        timeout=12,
    )
    cache: Cache = request.app.state.cache
    task_id = str(uuid.uuid4())
    await cache.set_message_id2task_id(message_id=str(message.id), task_id=task_id)
    await cache.set_task_id2data(task_id=task_id, data=TaskCacheData(
        status=TaskStatus.RUNNING,
        channel_id=str(discord_user_client.channel_id),
        guild_id=str(discord_user_client.guild_id),
        message_id=str(message.id)
    ))
    return {
        "success": interaction.successful,
        "task_id": task_id,
        "message_id": str(message.id)
    }


@app.post("/v1/video")
async def video_api(
        request: Request,
        video: UploadFile,
        model: VideoModel = Form(...),
        refer_mode: VideoReferMode = Form(...),
        length: VideoLength = Form(...),
        prompt: str = Form(...)
):
    # size_mb = video.size / 1024.0 / 1024.0
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client
    video_bytes = await video.read()
    interaction = await discord_user_client.video(
        prompt=prompt,
        video=io.BytesIO(video_bytes),
        model=model,
        refer_mode=refer_mode,
        length=length
    )
    print(f"video, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    message: discord.Message = await discord_user_client.wait_for(
        'message',
        check=lambda m: m.embeds and ('Generating' in m.embeds[0].description),
        timeout=12,
    )
    cache: Cache = request.app.state.cache
    task_id = str(uuid.uuid4())
    await cache.set_message_id2task_id(message_id=str(message.id), task_id=task_id)
    await cache.set_task_id2data(task_id=task_id, data=TaskCacheData(
        status=TaskStatus.RUNNING,
        channel_id=str(discord_user_client.channel_id),
        guild_id=str(discord_user_client.guild_id),
        message_id=str(message.id)
    ))
    return {
        "success": interaction.successful,
        "task_id": task_id,
        "message_id": str(message.id)
    }


@app.get("/v1/task-data/{task_id}")
async def task_data(
        request: Request,
        task_id: str,
):
    cache: Cache = request.app.state.cache
    data = await cache.get_task_data_by_id(task_id=task_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return data


@app.on_event("startup")
async def startup_event():
    if settings.redis_uri:
        redis = await RedisCache.init_redis_pool(redis_uri=settings.redis_uri)
        app.state.cache = RedisCache(redis=redis, prefix=settings.cache_prefix)
    else:
        app.state.cache = MemoryCache(prefix=settings.cache_prefix)

    discord_user_client = DiscordUserClient(
        guild_id=settings.discord_guild_id,
        channel_id=settings.discord_channel_id,
        application_id=settings.domoai_application_id,
        cache=app.state.cache
    )

    app.state.discord_user_client = discord_user_client
    await discord_user_client.login(settings.discord_token)
    app.state.discord_start_task = asyncio.create_task(discord_user_client.connect(reconnect=True))
    await discord_user_client.wait_until_ready()


@app.on_event("shutdown")
async def shutdown_event():
    if app.state.discord_start_task:
        app.state.discord_start_task.cancel()

    discord_user_client: DiscordUserClient = app.state.discord_user_client
    if not discord_user_client.is_closed():
        await discord_user_client.close()

    cache: Cache = app.state.cache
    await cache.close()
