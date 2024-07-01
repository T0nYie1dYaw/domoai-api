from __future__ import annotations

import enum
from typing import Optional, List, Dict

import discord
from pydantic import BaseModel


class Mode(enum.Enum):
    FAST = "fast"
    RELAX = "relax"


class AnimateIntensity(enum.Enum):
    LOW = "low"
    MEDIUM = "mid"
    HIGH = "high"


class AnimateLength(enum.Enum):
    LENGTH_3S = "3s"
    LENGTH_5S = "5s"


class BaseModelInfo(BaseModel):
    name: str
    prompt_args: str


class GenModelInfo(BaseModelInfo):
    pass


class MoveModelInfo(BaseModelInfo):
    pass


class VideoModelInfo(BaseModelInfo):
    allowed_refer_modes: List[VideoReferMode]
    allowed_lip_sync: bool
    allowed_reference_image: bool


class VideoReferMode(enum.Enum):
    REFER_TO_SOURCE_VIDEO_MORE = "VIDEO_MORE"
    REFER_TO_MY_PROMPT_MORE = "PROMPT_MORE"


class VideoKey(enum.Enum):
    WHITE = "WHITE"
    BLACK = "BLACK"
    RED = "RED"
    ORANGE = "ORANGE"
    YELLOW = "YELLOW"
    CYAN = "CYAN"
    GREEN = "GREEN"
    BLUE = "BLUE"
    PINK = "PINK"
    BROWN = "BROWN"
    PURPLE = "PURPLE"
    GREY = "GREY"
    GRAY = "GRAY"
    MAGENTA = "MAGENTA"
    NAVY = "NAVY"
    BEIGE = "BEIGE"
    GOLD = "GOLD"
    SILVER = "SILVER"


class VideoLength(enum.Enum):
    LENGTH_3S = "3s"
    LENGTH_5S = "5s"
    LENGTH_10S = "10s"
    LENGTH_20S = "20s"


class TaskAsset(BaseModel):
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    url: str
    proxy_url: str
    content_type: Optional[str] = None

    @staticmethod
    def from_attachment(attachment: discord.Attachment) -> TaskAsset:
        return TaskAsset(
            size=attachment.size,
            width=attachment.width,
            height=attachment.height,
            url=attachment.url,
            proxy_url=attachment.proxy_url,
            content_type=attachment.content_type
        )


class TaskStatus(enum.Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"


class TaskCommand(enum.Enum):
    GEN = "GEN"
    REAL = "REAL"
    MOVE = "MOVE"
    VIDEO = "VIDEO"
    ANIMATE = "ANIMATE"


class TaskCacheData(BaseModel):
    command: TaskCommand
    channel_id: str
    guild_id: Optional[str]
    message_id: str
    images: Optional[List[TaskAsset]] = None
    videos: Optional[List[TaskAsset]] = None
    status: TaskStatus
    upscale_custom_ids: Optional[Dict[str, str]] = None
    vary_custom_ids: Optional[Dict[str, str]] = None


class CreateTaskOut(BaseModel):
    success: bool
    task_id: str
    message_id: str


class TaskStateOut(BaseModel):
    command: TaskCommand
    channel_id: str
    guild_id: Optional[str]
    message_id: str
    images: Optional[List[TaskAsset]] = None
    videos: Optional[List[TaskAsset]] = None
    status: TaskStatus
    upscale_indices: Optional[List[int]] = None
    vary_indices: Optional[List[int]] = None

    @staticmethod
    def from_cache_data(data: TaskCacheData) -> TaskStateOut:
        upscale_index_map = {
            "U1": 1,
            "U2": 2,
            "U3": 3,
            "U4": 4
        }
        vary_index_map = {
            "V1": 1,
            "V2": 2,
            "V3": 3,
            "V4": 4
        }
        if data.upscale_custom_ids is not None:
            upscale_indices = []
            for key, value in data.upscale_custom_ids.items():
                index = upscale_index_map.get(key)
                if index is not None:
                    upscale_indices.append(index)
            upscale_indices.sort()
        else:
            upscale_indices = None
        if data.vary_custom_ids is not None:
            vary_indices = []
            for key, value in data.vary_custom_ids.items():
                index = vary_index_map.get(key)
                if index is not None:
                    vary_indices.append(index)
            vary_indices.sort()
        else:
            vary_indices = None

        return TaskStateOut(
            command=data.command,
            channel_id=data.channel_id,
            guild_id=data.guild_id,
            message_id=data.message_id,
            images=data.images,
            videos=data.videos,
            status=data.status,
            upscale_indices=upscale_indices,
            vary_indices=vary_indices
        )
