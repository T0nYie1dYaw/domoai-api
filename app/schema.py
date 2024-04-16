from __future__ import annotations

import enum
from typing import Optional, List

import discord
from pydantic import BaseModel


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


class TaskCacheData(BaseModel):
    channel_id: str
    guild_id: Optional[str]
    message_id: str
    images: Optional[List[TaskAsset]] = None
    videos: Optional[List[TaskAsset]] = None
    status: TaskStatus
