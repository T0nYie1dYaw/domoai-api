import asyncio
import re
from typing import Dict, List, Optional

import discord
from discord import ComponentType, InteractionType, InvalidData
from discord.http import Route
from discord.utils import _generate_nonce

from app.cache import Cache
from app.event_callback import EventCallback
from app.models import GenModel, MoveModel, VideoModel
from app.schema import VideoReferMode, VideoLength, TaskCacheData, TaskAsset, TaskStatus, \
    TaskCommand, AnimateIntensity, AnimateLength, Mode


class DiscordUserClient(discord.Client):

    def __init__(
            self,
            channel_id: int,
            guild_id: int,
            application_id: int,
            cache: Cache,
            event_callback_url: Optional[str],
            **options
    ):
        super().__init__(**options)
        self.event_callback = EventCallback(callback_url=event_callback_url)
        self.application_id = application_id
        self.commands: Dict[str, discord.SlashCommand] = {}

        self.guild_id = guild_id
        self.guild = None

        self.channel_id = channel_id
        self.channel = None
        self.cache = cache

        self.bot_user_id = None

    async def setup_hook(self):
        self.bot_user_id = self.user.id
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
        if after.author.id != self.application_id:
            return
        print(
            f"message edit, before {before}, after: {after}")
        if after.embeds:
            embed: discord.Embed = after.embeds[0]
            if embed.title.startswith('/gen'):
                await self.handle_gen_result(message=after)
            elif embed.title.startswith('/real'):
                await self.handle_real_result(message=after)
            elif embed.title == '/animate':
                await self.handle_animate_result(message=after)
            elif embed.title == '/video':
                await self.handle_video_result(message=after)
            elif embed.title == '/move':
                await self.handle_move_result(message=after)
        elif 'After:' in after.content and 'Before:' in after.content:
            await self.handle_video_result(message=after)
        elif 'Result:' in after.content and 'Image:' in after.content and 'Video:' in after.content:
            await self.handle_move_result(message=after)

    async def wait_for_generating_message(self, embeds_desc_keyword: str) -> discord.Message:
        def check(message: discord.Message):
            if not message.embeds or not message.mentions:
                return False
            if message.mentions[0].id != self.bot_user_id:
                return False
            return embeds_desc_keyword in message.embeds[0].description

        return await self.wait_for(
            'message',
            check=check,
            timeout=20
        )

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
        upscale_custom_ids = {}
        vary_custom_ids = {}
        for row in message.components:
            for component in row.children:
                if component.disabled or not component.label or not component.custom_id:
                    continue
                if component.label.startswith("U"):
                    upscale_custom_ids[component.label] = component.custom_id
                elif component.label.startswith("Vary"):
                    vary_custom_ids["V1"] = component.custom_id
                elif component.label.startswith("V"):
                    vary_custom_ids[component.label] = component.custom_id

        data = TaskCacheData(
            command=TaskCommand.GEN,
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            images=[TaskAsset.from_attachment(attachment)],
            status=TaskStatus.SUCCESS,
            upscale_custom_ids=upscale_custom_ids,
            vary_custom_ids=vary_custom_ids
        )
        await self.cache.set_task_id2data(task_id=task_id, data=data)
        await self.event_callback.send_task_success(task_id=task_id, data=data)

    async def handle_real_result(
            self,
            message: discord.Message
    ):
        if not message.attachments:
            return
        attachment = message.attachments[0]

        task_id = await self.cache.get_task_id_by_message_id(message_id=str(message.id))
        if not task_id:
            return
        upscale_custom_ids = {}
        vary_custom_ids = {}
        for row in message.components:
            for component in row.children:
                if component.disabled or not component.label or not component.custom_id:
                    continue
                if component.label.startswith("U"):
                    upscale_custom_ids[component.label] = component.custom_id
                elif component.label.startswith("Vary"):
                    vary_custom_ids["V1"] = component.custom_id
                elif component.label.startswith("V"):
                    vary_custom_ids[component.label] = component.custom_id

        data = TaskCacheData(
            command=TaskCommand.REAL,
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            images=[TaskAsset.from_attachment(attachment)],
            status=TaskStatus.SUCCESS,
            upscale_custom_ids=upscale_custom_ids,
            vary_custom_ids=vary_custom_ids
        )

        await self.cache.set_task_id2data(task_id=task_id, data=data)
        await self.event_callback.send_task_success(task_id=task_id, data=data)

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
            match = re.search(r"After:.*?(https:.*)", message.content)
            if not match:
                return
            video_url = match.group(1)
            asset = TaskAsset(
                url=video_url,
                proxy_url=video_url
            )

        data = TaskCacheData(
            command=TaskCommand.VIDEO,
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            videos=[asset],
            status=TaskStatus.SUCCESS
        )

        await self.cache.set_task_id2data(task_id=task_id, data=data)
        await self.event_callback.send_task_success(task_id=task_id, data=data)

    async def handle_animate_result(
            self,
            message: discord.Message
    ):
        task_id = await self.cache.get_task_id_by_message_id(message_id=str(message.id))
        if not task_id:
            return

        if not message.attachments:
            return

        attachment = message.attachments[0]
        asset = TaskAsset.from_attachment(attachment)

        data = TaskCacheData(
            command=TaskCommand.ANIMATE,
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            videos=[asset],
            status=TaskStatus.SUCCESS
        )
        await self.cache.set_task_id2data(task_id=task_id, data=data)
        await self.event_callback.send_task_success(task_id=task_id, data=data)

    async def handle_move_result(
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
            match = re.search(r"Result:.*?(https:.*)", message.content)
            if not match:
                return
            video_url = match.group(1)
            asset = TaskAsset(
                url=video_url,
                proxy_url=video_url
            )

        data = TaskCacheData(
            command=TaskCommand.MOVE,
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            videos=[asset],
            status=TaskStatus.SUCCESS
        )
        await self.cache.set_task_id2data(task_id=task_id, data=data)
        await self.event_callback.send_task_success(task_id=task_id, data=data)

    async def gen(
            self,
            prompt: str,
            image: Optional[discord.File] = None,
            mode: Optional[Mode] = None,
            model: Optional[GenModel] = None
    ) -> Optional[discord.Interaction]:
        command = self.commands.get('gen')
        if not command:
            return None
        request_prompt = prompt
        if mode:
            request_prompt += f" --{mode.value}"
        if model:
            request_prompt += f" --{model.value}"
        options = dict(
            prompt=request_prompt
        )
        if image:
            uploaded_image_files = await self.channel.upload_files(image)
            image.close()
            options['img2img'] = uploaded_image_files[0]

        interaction = await command(self.channel, **options)
        return interaction

    async def real(
            self,
            image: discord.File,
            prompt: Optional[str] = None,
            mode: Optional[Mode] = None
    ) -> Optional[discord.Interaction]:
        command = self.commands.get('real')
        if not command:
            return None
        uploaded_image_files = await self.channel.upload_files(image)
        image.close()
        options = dict(
            image=uploaded_image_files[0]
        )
        request_prompt_parts = []
        if prompt:
            request_prompt_parts.append(prompt)

        if mode:
            request_prompt_parts.append(f'--{mode.value}')

        if request_prompt_parts:
            options['prompt'] = ' '.join(request_prompt_parts)

        interaction = await command(self.channel, **options)
        return interaction

    async def click_button(
            self,
            custom_id: str,
            message_id: int
    ) -> Optional[discord.Interaction]:
        data = {
            "component_type": ComponentType.button.value,
            "custom_id": custom_id
        }

        nonce = _generate_nonce()

        try:
            payload = {
                'application_id': self.application_id,
                'channel_id': self.channel_id,
                'data': data,
                'nonce': nonce,
                'session_id': '44efec80d647a97968b4c60d26d3c032',
                'type': InteractionType.component.value,
                'guild_id': self.guild_id,
                'message_flags': 0,
                'message_id': message_id
            }
            await self.http.request(Route('POST', '/interactions'), json=payload, form=[], files=None)
            # await self.http.interact(
            #     type=InteractionType.component,
            #     nonce=nonce,
            #     data=data,
            #     channel=self.channel,
            #     application_id=self.application_id
            # )
            # The maximum possible time a response can take is 3 seconds,
            # +/- a few milliseconds for network latency
            # However, people have been getting errors because their gateway
            # disconnects while waiting for the interaction, causing the
            # response to be delayed until the gateway is reconnected
            # 12 seconds should be enough to account for this
            i = await self.wait_for(
                'interaction_finish',
                check=lambda d: d.nonce == nonce,
                timeout=12,
            )
            return i
        except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
            raise InvalidData('Did not receive a response from Discord') from exc

    async def move(
            self,
            image: discord.File,
            video: discord.File,
            prompt: str,
            model: MoveModel,
            length: VideoLength,
            mode: Optional[Mode] = None
    ) -> Optional[discord.Interaction]:
        command = self.commands.get('move')
        if not command:
            return None
        uploaded_images = await self.channel.upload_files(image)
        image.close()

        uploaded_videos = await self.channel.upload_files(video)
        video.close()
        request_prompt = f"{prompt} --{model.value} --length {length.value}"
        if mode:
            request_prompt += f' --{mode.value}'
        options = dict(
            prompt=request_prompt,
            video=uploaded_videos[0],
            image=uploaded_images[0]
        )
        return await command(self.channel, **options)

    async def video(
            self,
            video: discord.File,
            prompt: str,
            model: VideoModel,
            refer_mode: VideoReferMode,
            length: VideoLength,
            mode: Optional[Mode] = None
    ) -> Optional[discord.Interaction]:
        command = self.commands.get('video')
        if not command:
            return None
        uploaded_videos = await self.channel.upload_files(video)
        video.close()
        if refer_mode == VideoReferMode.REFER_TO_MY_PROMPT_MORE:
            refer_mode_value = 'p'
        else:
            refer_mode_value = 'v'
        request_prompt = f"{prompt} --{model.value} --refer {refer_mode_value} --length {length.value}"
        if mode:
            request_prompt += f' --{mode.value}'
        options = dict(
            prompt=request_prompt,
            video=uploaded_videos[0]
        )
        return await command(self.channel, **options)

    async def animate(
            self,
            image: discord.File,
            intensity: AnimateIntensity,
            length: AnimateLength,
            prompt: Optional[str] = None,
            mode: Optional[Mode] = None
    ) -> Optional[discord.Interaction]:
        command = self.commands.get('animate')
        if not command:
            return None
        uploaded_images = await self.channel.upload_files(image)
        image.close()
        request_prompt = f"--intensity {intensity.value} --length {length.value}"
        if prompt:
            request_prompt = f"{prompt} " + request_prompt
        if mode:
            request_prompt += f' --{mode.value}'
        options = dict(
            prompt=request_prompt,
            image=uploaded_images[0]
        )
        return await command(self.channel, **options)
