from __future__ import annotations

import enum
from typing import Optional, List, Dict

import discord
from pydantic import BaseModel


class AnimateIntensity(enum.Enum):
    LOW = "low"
    MEDIUM = "mid"
    HIGH = "high"


class AnimateLength(enum.Enum):
    LENGTH_3S = "3s"
    LENGTH_5S = "5s"


class VideoModel(enum.Enum):
    FS_V1 = "fs v1"
    ANI_V1_1 = "ani v1.1"
    ANI_V4_1 = "ani v4.1"
    ANI_V5_1 = "ani v5.1"
    ANI_V6 = "ani v6"
    ANI_V1 = "ani v1"
    ANI_V2 = "ani v2"
    ANI_V3 = "ani v3"
    ANI_V4 = "ani v4"
    ILLUS_V1_1 = "illus v1.1"
    ILLUS_V3_1 = "illus v3.1"
    ILLUS_V7_1 = "illus v7.1"
    ILLUS_V1 = "illus v1"
    ILLUS_V2 = "illus v2"
    ILLUS_V3 = "illus v3"
    ILLUS_V4 = "illus v4"
    ILLUS_V5 = "illus v5"
    ILLUS_V6 = "illus v6"
    ILLUS_V7 = "illus v7"
    ILLUS_V8 = "illus v8"


class MoveModel(enum.Enum):
    REAL_V1 = "real v1"
    ANI_V6 = "ani v6"
    ANI_V2 = "ani v2"
    ANI_V1_1 = "ani v1.1"


class VideoReferMode(enum.Enum):
    REFER_TO_SOURCE_VIDEO_MORE = "VIDEO_MORE"
    REFER_TO_MY_PROMPT_MORE = "PROMPT_MORE"


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
