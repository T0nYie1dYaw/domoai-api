import asyncio
import io
import uuid
from typing import Optional

import discord
from fastapi import FastAPI, Request, UploadFile, Form, HTTPException
from starlette import status

from app.cache import RedisCache, MemoryCache, Cache
from app.schema import VideoModel, VideoReferMode, VideoLength, TaskCacheData, TaskStatus, CreateTaskOut, MoveModel, \
    TaskCommand, TaskStateOut, AnimateLength, AnimateIntensity, Mode, GenModel
from app.settings import get_settings
from app.user_client import DiscordUserClient

app = FastAPI()

settings = get_settings()


async def __did_send_interaction(
        wait_message_desc_keyword: str,
        discord_user_client: DiscordUserClient,
        cache: Cache,
        command: TaskCommand
) -> CreateTaskOut:
    message: discord.Message = await discord_user_client.wait_for_generating_message(
        embeds_desc_keyword=wait_message_desc_keyword
    )
    task_id = str(uuid.uuid4())
    await cache.set_message_id2task_id(message_id=str(message.id), task_id=task_id)
    await cache.set_task_id2data(task_id=task_id, data=TaskCacheData(
        command=command,
        status=TaskStatus.RUNNING,
        channel_id=str(discord_user_client.channel_id),
        guild_id=str(discord_user_client.guild_id),
        message_id=str(message.id)
    ))
    return CreateTaskOut(
        success=True,
        task_id=task_id,
        message_id=str(message.id)
    )


@app.post("/v1/gen")
async def gen_api(
        request: Request,
        image: Optional[UploadFile] = None,
        prompt: str = Form(...),
        mode: Optional[Mode] = Form(default=None),
        model: Optional[GenModel] = Form(default=None)
):
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client
    if image:
        image_bytes = await image.read()
        image_file = discord.File(io.BytesIO(image_bytes), filename=image.filename)
    else:
        image_file = None
    interaction = await discord_user_client.gen(prompt=prompt, image=image_file, mode=mode, model=model)
    print(f"gen, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    result = await __did_send_interaction(
        wait_message_desc_keyword='Waiting to start',
        command=TaskCommand.GEN,
        cache=request.app.state.cache,
        discord_user_client=discord_user_client
    )
    return result


@app.post("/v1/real")
async def real_api(
        request: Request,
        image: UploadFile = Form(...),
        prompt: Optional[str] = Form(default=None),
        mode: Optional[Mode] = Form(default=None)
):
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client
    image_bytes = await image.read()
    image_file = discord.File(io.BytesIO(image_bytes), filename=image.filename)
    interaction = await discord_user_client.real(prompt=prompt, image=image_file, mode=mode)
    print(f"real, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    result = await __did_send_interaction(
        wait_message_desc_keyword='Waiting to start',
        command=TaskCommand.REAL,
        cache=request.app.state.cache,
        discord_user_client=discord_user_client
    )
    return result


@app.post("/v1/animate")
async def animate_api(
        request: Request,
        image: UploadFile = Form(...),
        length: AnimateLength = Form(...),
        intensity: AnimateIntensity = Form(...),
        prompt: Optional[str] = Form(default=None),
        mode: Optional[Mode] = Form(default=None)
):
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client
    image_bytes = await image.read()
    image_file = discord.File(io.BytesIO(image_bytes), filename=image.filename)
    interaction = await discord_user_client.animate(
        prompt=prompt,
        image=image_file,
        length=length,
        intensity=intensity,
        mode=mode
    )
    print(f"animate, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    result = await __did_send_interaction(
        wait_message_desc_keyword='Waiting to start',
        command=TaskCommand.ANIMATE,
        cache=request.app.state.cache,
        discord_user_client=discord_user_client
    )
    return result


@app.post("/v1/upscale")
async def upscale_api(
        request: Request,
        task_id: str = Form(...),
        index: int = Form(..., ge=1, le=4)
):
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client

    cache: Cache = request.app.state.cache
    data = await cache.get_task_data_by_id(task_id=task_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    label = f"U{index}"
    custom_id = data.upscale_custom_ids.get(label)
    if not custom_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    interaction = await discord_user_client.click_button(custom_id=custom_id, message_id=int(data.message_id))
    print(f"upscale, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    result = await __did_send_interaction(
        wait_message_desc_keyword='Waiting to start',
        command=TaskCommand.GEN,
        cache=request.app.state.cache,
        discord_user_client=discord_user_client
    )
    return result


@app.post("/v1/vary")
async def vary_api(
        request: Request,
        task_id: str = Form(...),
        index: int = Form(..., ge=1, le=4)
):
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client

    cache: Cache = request.app.state.cache
    data = await cache.get_task_data_by_id(task_id=task_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    label = f"V{index}"
    custom_id = data.vary_custom_ids.get(label)
    if not custom_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    interaction = await discord_user_client.click_button(custom_id=custom_id, message_id=int(data.message_id))
    print(f"vary, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    result = await __did_send_interaction(
        wait_message_desc_keyword='Waiting to start',
        command=TaskCommand.GEN,
        cache=request.app.state.cache,
        discord_user_client=discord_user_client
    )
    return result


@app.post("/v1/video")
async def video_api(
        request: Request,
        video: UploadFile,
        model: VideoModel = Form(...),
        refer_mode: VideoReferMode = Form(...),
        length: VideoLength = Form(...),
        prompt: str = Form(...),
        mode: Optional[Mode] = Form(default=None)
):
    # size_mb = video.size / 1024.0 / 1024.0
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client
    video_bytes = await video.read()
    video_file = discord.File(io.BytesIO(video_bytes), filename=video.filename)
    interaction = await discord_user_client.video(
        prompt=prompt,
        video=video_file,
        model=model,
        refer_mode=refer_mode,
        length=length,
        mode=mode
    )
    print(f"video, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    result = await __did_send_interaction(
        wait_message_desc_keyword='Generating',
        command=TaskCommand.VIDEO,
        cache=request.app.state.cache,
        discord_user_client=discord_user_client
    )
    return result


@app.post("/v1/move")
async def move_api(
        request: Request,
        image: UploadFile,
        video: UploadFile,
        model: MoveModel = Form(...),
        length: VideoLength = Form(...),
        prompt: str = Form(...),
        mode: Optional[Mode] = Form(default=None)
):
    # size_mb = video.size / 1024.0 / 1024.0
    discord_user_client: DiscordUserClient = request.app.state.discord_user_client
    image_bytes = await image.read()
    image_file = discord.File(io.BytesIO(image_bytes), filename=image.filename)
    video_bytes = await video.read()
    video_file = discord.File(io.BytesIO(video_bytes), filename=video.filename)
    interaction = await discord_user_client.move(
        prompt=prompt,
        image=image_file,
        video=video_file,
        model=model,
        length=length,
        mode=mode
    )
    print(f"move, interaction_id: {interaction.id}, interaction.nonce: {interaction.nonce}")

    if not interaction.successful:
        # TODO:
        return {"success": interaction.successful}

    result = await __did_send_interaction(
        wait_message_desc_keyword='Generating',
        command=TaskCommand.MOVE,
        cache=request.app.state.cache,
        discord_user_client=discord_user_client
    )
    return result


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
    return TaskStateOut.from_cache_data(data=data)


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
