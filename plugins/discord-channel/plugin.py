"""discord-channel: Discord IM adapter plugin for OpenAkita.

Connects OpenAkita to Discord via the official Bot API (discord.py).
Supports guild text channels, DMs, threads, images, files, edit-in-place
streaming, Markdown, and @mention detection.
"""

from __future__ import annotations

import asyncio
import io
import logging
import tempfile
import time
from pathlib import Path
from typing import Any

from openakita.channels.base import ChannelAdapter
from openakita.channels.types import (
    MediaFile,
    MediaStatus,
    MessageContent,
    MessageType,
    OutgoingMessage,
    UnifiedMessage,
)
from openakita.plugins.api import PluginAPI, PluginBase

logger = logging.getLogger(__name__)

discord = None
_discord_imported = False


def _import_discord():
    global discord, _discord_imported
    if _discord_imported:
        return
    try:
        import discord as _dc
        discord = _dc
        _discord_imported = True
    except ImportError:
        raise ImportError(
            "discord.py is not installed. Run: pip install discord.py>=2.3.0"
        )


DISCORD_MAX_MSG_LEN = 2000
DISCORD_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB (non-Nitro)


class DiscordAdapter(ChannelAdapter):
    """Discord Bot adapter using discord.py gateway + REST."""

    channel_name = "discord"

    capabilities = {
        **ChannelAdapter.capabilities,
        "streaming": True,
        "send_image": True,
        "send_file": True,
        "send_voice": False,
        "delete_message": True,
        "edit_message": True,
        "get_chat_info": True,
        "get_user_info": True,
        "get_chat_members": True,
        "get_recent_messages": True,
        "markdown": True,
    }

    def __init__(
        self,
        creds: dict,
        *,
        channel_name: str,
        bot_id: str,
        agent_profile_id: str,
    ) -> None:
        super().__init__(
            channel_name=channel_name,
            bot_id=bot_id,
            agent_profile_id=agent_profile_id,
        )
        self._creds = creds
        self._bot_token: str = creds.get("bot_token", "")

        self._allowed_guild_ids: set[str] = set(creds.get("allowed_guild_ids", []))
        self._allowed_channel_ids: set[str] = set(creds.get("allowed_channel_ids", []))
        self._respond_to_dms: bool = creds.get("respond_to_dms", True)
        self._respond_to_mentions_only: bool = creds.get("respond_to_mentions_only", True)
        self._command_prefix: str = creds.get("command_prefix", "")
        self._streaming_throttle_ms: int = creds.get("streaming_throttle_ms", 1500)
        self._max_message_length: int = min(creds.get("max_message_length", 2000), DISCORD_MAX_MSG_LEN)
        self._status_message: str = creds.get("status_message", "Powered by OpenAkita")

        self._client: Any = None
        self._client_task: asyncio.Task | None = None
        self._ready_event: asyncio.Event = asyncio.Event()

        self._streaming_buffers: dict[str, str] = {}
        self._streaming_msg_ids: dict[str, int] = {}
        self._streaming_last_patch: dict[str, float] = {}
        self._typing_start_time: dict[str, float] = {}

        self._media_dir = Path(tempfile.gettempdir()) / "openakita-discord-media"
        self._media_dir.mkdir(parents=True, exist_ok=True)

    # ─────────── Lifecycle ───────────

    async def start(self) -> None:
        _import_discord()

        if not self._bot_token:
            raise ValueError(
                "Discord bot token is required. Set 'bot_token' in channel credentials "
                "or the DISCORD_BOT_TOKEN environment variable."
            )

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        self._client = discord.Client(intents=intents)
        self._register_event_handlers()

        self._client_task = asyncio.create_task(self._run_client())
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("Discord client did not become ready within 30s, continuing anyway")

        self._running = True
        logger.info("DiscordAdapter started (guilds=%s)", self._allowed_guild_ids or "all")

    async def _run_client(self) -> None:
        try:
            await self._client.start(self._bot_token)
        except discord.LoginFailure:
            logger.error("Discord login failed — check your bot token")
        except Exception as e:
            logger.error("Discord client error: %s", e, exc_info=True)

    def _register_event_handlers(self) -> None:
        client = self._client

        @client.event
        async def on_ready():
            logger.info(
                "Discord bot logged in as %s (id=%s) in %d guilds",
                client.user, client.user.id, len(client.guilds),
            )
            if self._status_message:
                try:
                    await client.change_presence(
                        activity=discord.Game(name=self._status_message)
                    )
                except Exception:
                    pass
            self._ready_event.set()

        @client.event
        async def on_message(message: Any):
            await self._handle_message(message)

    async def stop(self) -> None:
        self._running = False
        if self._client and not self._client.is_closed():
            await self._client.close()
        if self._client_task and not self._client_task.done():
            self._client_task.cancel()
            try:
                await self._client_task
            except (asyncio.CancelledError, Exception):
                pass
            self._client_task = None
        logger.info("DiscordAdapter stopped")

    # ─────────── Inbound message handling ───────────

    async def _handle_message(self, message: Any) -> None:
        if not self._client or not self._client.user:
            return
        if message.author.id == self._client.user.id:
            return
        if message.author.bot:
            return

        is_dm = message.guild is None

        if is_dm and not self._respond_to_dms:
            return

        if not is_dm:
            guild_id = str(message.guild.id)
            channel_id = str(message.channel.id)
            if self._allowed_guild_ids and guild_id not in self._allowed_guild_ids:
                return
            if self._allowed_channel_ids and channel_id not in self._allowed_channel_ids:
                return

        is_mentioned = False
        if not is_dm and self._client.user:
            is_mentioned = self._client.user.mentioned_in(message)
            if message.reference and message.reference.resolved:
                ref_msg = message.reference.resolved
                if hasattr(ref_msg, "author") and ref_msg.author.id == self._client.user.id:
                    is_mentioned = True

        if not is_dm and self._respond_to_mentions_only and not is_mentioned:
            if self._command_prefix and message.content.startswith(self._command_prefix):
                pass  # allow prefix commands through
            else:
                return

        unified = await self._convert_message(message, is_dm, is_mentioned)
        self._log_message(unified)
        await self._emit_message(unified)

    async def _convert_message(
        self, message: Any, is_dm: bool, is_mentioned: bool,
    ) -> UnifiedMessage:
        content = MessageContent()

        text = message.content or ""
        if self._client and self._client.user:
            bot_mention = f"<@{self._client.user.id}>"
            bot_mention_nick = f"<@!{self._client.user.id}>"
            text = text.replace(bot_mention, "").replace(bot_mention_nick, "").strip()
        content.text = text

        for attachment in message.attachments:
            media = MediaFile.create(
                filename=attachment.filename,
                mime_type=attachment.content_type or "application/octet-stream",
                url=attachment.url,
                size=attachment.size,
            )
            media.width = attachment.width
            media.height = attachment.height
            ct = (attachment.content_type or "").lower()
            if ct.startswith("image/"):
                content.images.append(media)
            elif ct.startswith("video/"):
                content.videos.append(media)
            elif ct.startswith("audio/"):
                content.voices.append(media)
            else:
                content.files.append(media)

        for sticker in getattr(message, "stickers", []):
            content.sticker = {
                "id": str(sticker.id),
                "emoji": sticker.name,
                "set_name": getattr(sticker, "pack_id", None),
            }
            break

        chat_type = "private" if is_dm else "group"
        chat_id = str(message.channel.id)

        thread_id = None
        if hasattr(message.channel, "parent_id") and message.channel.parent_id:
            thread_id = str(message.channel.id)
            chat_id = str(message.channel.parent_id)

        user = message.author
        display_name = getattr(user, "display_name", None) or user.name

        reply_to = None
        if message.reference and message.reference.message_id:
            reply_to = str(message.reference.message_id)

        return UnifiedMessage.create(
            channel=self.channel_name,
            channel_message_id=str(message.id),
            user_id=f"dc_{user.id}",
            channel_user_id=str(user.id),
            chat_id=chat_id,
            content=content,
            chat_type=chat_type,
            thread_id=thread_id,
            is_mentioned=is_mentioned or is_dm,
            is_direct_message=is_dm,
            reply_to=reply_to,
            raw={
                "message_id": message.id,
                "channel_id": message.channel.id,
                "guild_id": message.guild.id if message.guild else None,
                "user_id": user.id,
                "username": user.name,
                "discriminator": getattr(user, "discriminator", "0"),
            },
            metadata={
                "is_group": not is_dm,
                "sender_name": display_name,
                "chat_name": (
                    getattr(message.channel, "name", None)
                    or display_name
                ),
                "guild_name": message.guild.name if message.guild else None,
            },
        )

    # ─────────── Outbound message sending ───────────

    async def send_message(self, message: OutgoingMessage) -> str:
        if not self._client:
            raise RuntimeError("Discord client not started")

        channel = self._client.get_channel(int(message.chat_id))
        if channel is None:
            try:
                channel = await self._client.fetch_channel(int(message.chat_id))
            except Exception as e:
                logger.error("Failed to fetch Discord channel %s: %s", message.chat_id, e)
                raise

        text = message.content.text or ""
        reply_ref = None
        if message.reply_to:
            try:
                reply_ref = discord.MessageReference(
                    message_id=int(message.reply_to),
                    channel_id=channel.id,
                )
            except (ValueError, TypeError):
                pass

        files_to_send: list[Any] = []
        for media in message.content.all_media:
            dc_file = await self._media_to_discord_file(media)
            if dc_file:
                files_to_send.append(dc_file)

        sent = None

        if not text and not files_to_send:
            text = "(empty message)"

        chunks = self._split_message(text)
        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            kwargs: dict[str, Any] = {"content": chunk}
            if i == 0 and reply_ref:
                kwargs["reference"] = reply_ref
            if is_last and files_to_send:
                kwargs["files"] = files_to_send
            try:
                sent = await channel.send(**kwargs)
            except discord.HTTPException as e:
                logger.error("Discord send_message failed: %s", e)
                raise

        return str(sent.id) if sent else ""

    async def _media_to_discord_file(self, media: MediaFile) -> Any:
        _import_discord()
        try:
            if media.local_path and Path(media.local_path).is_file():
                return discord.File(media.local_path, filename=media.filename)
            if media.url:
                import httpx
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(media.url)
                    resp.raise_for_status()
                    return discord.File(
                        io.BytesIO(resp.content),
                        filename=media.filename,
                    )
        except Exception as e:
            logger.warning("Failed to prepare Discord file %s: %s", media.filename, e)
        return None

    def _split_message(self, text: str) -> list[str]:
        if not text:
            return [""]
        limit = self._max_message_length
        if len(text) <= limit:
            return [text]

        chunks: list[str] = []
        while text:
            if len(text) <= limit:
                chunks.append(text)
                break
            split_at = text.rfind("\n", 0, limit)
            if split_at == -1 or split_at < limit // 2:
                split_at = limit
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")
        return chunks

    # ─────────── Media handling ───────────

    async def download_media(self, media: MediaFile) -> Path:
        if media.local_path and Path(media.local_path).is_file():
            return Path(media.local_path)

        if not media.url:
            raise ValueError("Discord media has no URL to download from")

        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(media.url)
            resp.raise_for_status()
            local_path = self._media_dir / media.filename
            local_path.write_bytes(resp.content)
            media.local_path = str(local_path)
            media.status = MediaStatus.READY
            return local_path

    async def upload_media(self, path: Path, mime_type: str) -> MediaFile:
        return MediaFile.create(filename=path.name, mime_type=mime_type)

    # ─────────── Streaming (edit-in-place) ───────────

    def is_streaming_enabled(self, is_group: bool = False) -> bool:
        return self._client is not None

    async def stream_token(
        self,
        chat_id: str,
        token: str,
        *,
        thread_id: str | None = None,
        is_group: bool = False,
    ) -> None:
        sk = self._make_session_key(chat_id, thread_id)
        self._streaming_buffers[sk] = self._streaming_buffers.get(sk, "") + token

        now = time.time()
        last_t = self._streaming_last_patch.get(sk, 0.0)
        if now - last_t < self._streaming_throttle_ms / 1000.0:
            return

        buf = self._streaming_buffers.get(sk, "")
        display = buf[:self._max_message_length - 2] + " ▍" if buf else "▍"
        msg_id = self._streaming_msg_ids.get(sk)

        target_id = int(thread_id or chat_id)
        channel = self._client.get_channel(target_id) if self._client else None
        if not channel:
            return

        try:
            if msg_id:
                msg = channel.get_partial_message(msg_id)
                await msg.edit(content=display)
            else:
                sent = await channel.send(content=display)
                self._streaming_msg_ids[sk] = sent.id
            self._streaming_last_patch[sk] = now
        except Exception as e:
            logger.debug("Discord stream_token edit failed: %s", e)

    async def finalize_stream(
        self,
        chat_id: str,
        final_text: str,
        *,
        thread_id: str | None = None,
    ) -> bool:
        sk = self._make_session_key(chat_id, thread_id)
        msg_id = self._streaming_msg_ids.pop(sk, None)
        self._streaming_buffers.pop(sk, None)
        self._streaming_last_patch.pop(sk, None)

        if not msg_id or not self._client:
            return False

        target_id = int(thread_id or chat_id)
        channel = self._client.get_channel(target_id)
        if not channel:
            return False

        chunks = self._split_message(final_text)
        try:
            first_msg = channel.get_partial_message(msg_id)
            await first_msg.edit(content=chunks[0])
            for extra_chunk in chunks[1:]:
                await channel.send(content=extra_chunk)
            return True
        except Exception as e:
            logger.warning("Discord finalize_stream failed: %s", e)
            return False

    # ─────────── Optional capabilities ───────────

    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        if not self._client:
            return False
        try:
            channel = self._client.get_channel(int(chat_id))
            if not channel:
                channel = await self._client.fetch_channel(int(chat_id))
            msg = await channel.fetch_message(int(message_id))
            await msg.delete()
            return True
        except Exception as e:
            logger.error("Discord delete_message failed: %s", e)
            return False

    async def edit_message(self, chat_id: str, message_id: str, new_content: str) -> bool:
        if not self._client:
            return False
        try:
            channel = self._client.get_channel(int(chat_id))
            if not channel:
                channel = await self._client.fetch_channel(int(chat_id))
            msg = await channel.fetch_message(int(message_id))
            await msg.edit(content=new_content)
            return True
        except Exception as e:
            logger.error("Discord edit_message failed: %s", e)
            return False

    async def get_chat_info(self, chat_id: str) -> dict | None:
        if not self._client:
            return None
        try:
            channel = self._client.get_channel(int(chat_id))
            if not channel:
                channel = await self._client.fetch_channel(int(chat_id))
            guild = getattr(channel, "guild", None)
            return {
                "id": str(channel.id),
                "type": str(channel.type),
                "title": getattr(channel, "name", None) or str(channel.id),
                "guild_id": str(guild.id) if guild else None,
                "guild_name": guild.name if guild else None,
            }
        except Exception as e:
            logger.error("Discord get_chat_info failed: %s", e)
            return None

    async def get_user_info(self, user_id: str) -> dict | None:
        if not self._client:
            return None
        try:
            uid = int(user_id.removeprefix("dc_"))
            user = self._client.get_user(uid)
            if not user:
                user = await self._client.fetch_user(uid)
            return {
                "id": str(user.id),
                "username": user.name,
                "display_name": user.display_name,
                "avatar_url": str(user.display_avatar.url) if user.display_avatar else None,
                "bot": user.bot,
            }
        except Exception as e:
            logger.error("Discord get_user_info failed: %s", e)
            return None

    async def get_chat_members(self, chat_id: str) -> list[dict]:
        if not self._client:
            return []
        try:
            channel = self._client.get_channel(int(chat_id))
            if not channel or not hasattr(channel, "members"):
                return []
            return [
                {
                    "id": str(m.id),
                    "username": m.name,
                    "display_name": m.display_name,
                    "bot": m.bot,
                }
                for m in channel.members[:100]
            ]
        except Exception as e:
            logger.error("Discord get_chat_members failed: %s", e)
            return []

    async def get_recent_messages(self, chat_id: str, limit: int = 20) -> list[dict]:
        if not self._client:
            return []
        try:
            channel = self._client.get_channel(int(chat_id))
            if not channel:
                channel = await self._client.fetch_channel(int(chat_id))
            messages = []
            async for msg in channel.history(limit=min(limit, 100)):
                messages.append({
                    "id": str(msg.id),
                    "author": msg.author.name,
                    "content": msg.content[:500],
                    "timestamp": msg.created_at.isoformat(),
                })
            return messages
        except Exception as e:
            logger.error("Discord get_recent_messages failed: %s", e)
            return []

    async def send_typing(self, chat_id: str, thread_id: str | None = None) -> None:
        if not self._client:
            return
        target_id = int(thread_id or chat_id)
        try:
            channel = self._client.get_channel(target_id)
            if channel:
                await channel.typing()
        except Exception:
            pass
        sk = self._make_session_key(chat_id, thread_id)
        if sk not in self._typing_start_time:
            self._typing_start_time[sk] = time.time()

    async def clear_typing(self, chat_id: str, thread_id: str | None = None) -> None:
        sk = self._make_session_key(chat_id, thread_id)
        self._typing_start_time.pop(sk, None)

    @staticmethod
    def _make_session_key(chat_id: str, thread_id: str | None = None) -> str:
        return f"{chat_id}:{thread_id}" if thread_id else chat_id


# ─────────── Factory ───────────

def _discord_factory(
    creds: dict,
    *,
    channel_name: str,
    bot_id: str,
    agent_profile_id: str,
) -> DiscordAdapter:
    return DiscordAdapter(
        creds,
        channel_name=channel_name,
        bot_id=bot_id,
        agent_profile_id=agent_profile_id,
    )


# ─────────── Plugin entry point ───────────

class Plugin(PluginBase):
    def __init__(self) -> None:
        self._api: PluginAPI | None = None

    def on_load(self, api: PluginAPI) -> None:
        self._api = api
        api.register_channel("discord", _discord_factory)
        api.log("discord-channel v1.0.0 loaded (Bot API via discord.py)")

    def on_unload(self) -> None:
        self._api = None
