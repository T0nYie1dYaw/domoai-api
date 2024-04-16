import io
import os
import re
from typing import Dict, List, Optional, Any, Union

import discord

from app.cache import Cache
from app.schema import VideoModel, VideoReferMode, VideoLength, TaskCacheData, TaskAsset, TaskStatus


class DiscordUserClient(discord.Client):

    def __init__(self, channel_id: int, guild_id: int, application_id: int, cache: Cache, **options):
        super().__init__(**options)
        self.application_id = application_id
        self.commands: Dict[str, discord.SlashCommand] = {}

        self.guild_id = guild_id
        self.guild = None

        self.channel_id = channel_id
        self.channel = None
        self.cache = cache

    async def setup_hook(self):
        self.guild = await self.fetch_guild(self.guild_id)
        self.channel = await self.fetch_channel(self.channel_id)
        await self.__init_slash_commands()

        print(f'guild: {self.guild}')
        print(f'channel: {self.channel}')
        print(f'slash commands: {self.commands.keys()}')

    async def on_ready(self):
        print(f'Logged on as {self.user}')

    async def __init_slash_commands(self):
        commands: List[discord.SlashCommand] = [
            x for x in await self.guild.application_commands() if
            isinstance(x, discord.SlashCommand) and str(x.application_id) == str(self.application_id)
        ]
        for command in commands:
            self.commands[command.name] = command

    async def on_message(self, message: discord.Message):
        # if message.application_id != self.application_id:
        #     return

        print(
            f"message: {message}, interaction_id: {message.interaction.id if message.interaction else None}, interaction.nonce: {message.interaction.nonce if message.interaction else None}")

        if message.content == 'ping':
            await message.channel.send('pong')

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        print(
            f"message edit, before {before}, after: {after}")
        if not after.embeds:
            return
        embed: discord.Embed = after.embeds[0]
        if embed.title == '/gen':
            await self.handle_gen_result(message=after)
        elif embed.title == '/video':
            await self.handle_video_result(message=after)

    async def handle_gen_result(
            self,
            message: discord.Message
    ):
        if not message.attachments:
            return
        attachment = message.attachments[0]

        task_id = await self.cache.get_task_id_by_message_id(message_id=str(message.id))
        if not task_id:
            return

        await self.cache.set_task_id2data(task_id=task_id, data=TaskCacheData(
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            images=[TaskAsset.from_attachment(attachment)],
            status=TaskStatus.SUCCESS
        ))

    async def handle_video_result(
            self,
            message: discord.Message
    ):
        task_id = await self.cache.get_task_id_by_message_id(message_id=str(message.id))
        if not task_id:
            return

        if message.attachments:
            attachment = message.attachments[0]
            asset = TaskAsset.from_attachment(attachment)
        else:
            match = re.match(r"After:.*?(https:.*)", message.content)
            if not match:
                return
            video_url = match.group(1)
            asset = TaskAsset(
                url=video_url,
                proxy_url=video_url
            )

        await self.cache.set_task_id2data(task_id=task_id, data=TaskCacheData(
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            videos=[asset],
            status=TaskStatus.SUCCESS
        ))

    async def gen(self, prompt: str, image_url: Optional[str] = None) -> Optional[discord.Interaction]:
        command = self.commands.get('gen')
        if not command:
            return None
        options = dict(
            prompt=prompt
        )
        if image_url:
            image_file = discord.File(image_url)
            uploaded_image_files = await self.channel.upload_files(image_file)
            options['img2img'] = uploaded_image_files[0]

        interaction = await command(self.channel, **options)
        return interaction

    async def video(
            self,
            video: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase],
            prompt: str,
            model: VideoModel,
            refer_mode: VideoReferMode,
            length: VideoLength
    ) -> Optional[discord.Interaction]:
        command = self.commands.get('video')
        if not command:
            return None
        video_file = discord.File(video)
        uploaded_videos = await self.channel.upload_files(video_file)
        video_file.close()
        if refer_mode == VideoReferMode.REFER_TO_MY_PROMPT_MORE:
            refer_mode_value = 'p'
        else:
            refer_mode_value = 'v'
        options = dict(
            prompt=f"{prompt} --{model.value} --refer {refer_mode_value} --length {length.value}",
            video=uploaded_videos[0]
        )
        return await command(self.channel, **options)
