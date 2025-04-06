import os
import logging
import json
import discord
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# !!TODO: We are using config.json and pending_notification.json files to store config data and the queue system.
# This is for demo purposes only, in actual implementation there will be a more solid queue system and config data to be stored in Supabase.

# Add the project root to path to ensure imports work correctly
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.events.enums import EventType  # noqa

load_dotenv()

logger = logging.getLogger(__name__)

class DevrAIDiscordBot:
    def __init__(self):
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.notifications_file = os.path.join(os.path.dirname(__file__), "pending_notifications.json")
        self.config = self.load_config()
        logger.info(f"Loaded config: {self.config}")

        if not self.token:
            logger.warning("No Discord token found in env file. Bot can't connect.")

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.bot = discord.Bot(intents=intents)
        self.setup_event_handlers()
        self.register_commands()

        self.bot.loop.create_task(self.check_pending_notifications())

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Config loaded from file: {config}")
                return config
            else:
                default_config = {
                    "notification_channel_id": None,
                    "webhook_url": None,
                    "maintainers": []
                }
                self.save_config(default_config)
                logger.info(f"Default config created and saved: {default_config}")
                return default_config
        except Exception as e:
            logger.error(f"Config loading error: {str(e)}")
            return {"notification_channel_id": None, "webhook_url": None, "maintainers": []}

    def save_config(self, config=None):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config or self.config, f, indent=4)
            logger.info(f"Config saved to file: {config or self.config}")
            return True
        except Exception as e:
            logger.error(f"Config saving error: {str(e)}")
            return False

    async def check_pending_notifications(self):
        await self.bot.wait_until_ready()
        logger.info("Checking for pending notifications")

        while not self.bot.is_closed():
            try:
                if os.path.exists(self.notifications_file):
                    with open(self.notifications_file, 'r') as f:
                        try:
                            notifications = json.load(f)
                            pending = notifications.get("pending", [])

                            if pending:
                                logger.info(f"Found {len(pending)} pending notifications")

                                processed = []
                                for i, notification in enumerate(pending):
                                    event_type = notification.get("type")
                                    data = notification.get("data", {})

                                    success = await self.notify_github_event(event_type, data)

                                    if success:
                                        processed.append(i)
                                        logger.info(f"Processed {event_type} notification")
                                    else:
                                        logger.warning(f"Failed to process {event_type} notification")

                                if processed:
                                    notifications["pending"] = [n for i, n in enumerate(pending) if i not in processed]
                                    with open(self.notifications_file, 'w') as f_write:
                                        json.dump(notifications, f_write, indent=4)
                                    logger.info(f"Removed {len(processed)} processed notifications")
                        except json.JSONDecodeError:
                            logger.error("Invalid JSON in notifications file")
            except Exception as e:
                logger.error(f"Error checking notifications: {str(e)}")

            await asyncio.sleep(5)

    def setup_event_handlers(self):
        @self.bot.event
        async def on_ready():
            logger.info(f"Bot logged in as {self.bot.user}")

        @self.bot.event
        async def on_member_join(member):
            logger.info(f"New member joined: {member.name}")

            welcome_message = (
                f"Hey {member.mention}! Welcome to our community!\n\n"
                f"We're glad you're here at Devr.AI! Feel free to introduce yourself "
                f"and check out our channels.\n\n"
                f"If you need help with anything, just ask!"
            )

            general_channels = [channel for channel in member.guild.channels
                                if isinstance(channel, discord.TextChannel) and
                                any(name in channel.name.lower() for name in ["general", "welcome", "lobby", "introduction"])]

            if general_channels:
                try:
                    await general_channels[0].send(welcome_message)
                except Exception as e:
                    logger.error(f"Failed to send welcome message: {str(e)}")
            else:
                logger.warning("No suitable channel found for welcome message")

    def register_commands(self):
        devr_group = discord.SlashCommandGroup("devr", "Commands for Devr.AI bot")

        @self.bot.slash_command(name="help", description="Show available commands")
        async def help_command(ctx):
            help_text = """
            **Devr.AI Bot Commands**
            
            `/help` - Show this help message
            `/devr status` - Check if the bot is alive
            `/devr configure_channel` - Set up this channel for GitHub notifications
            `/devr register_maintainer` - Add yourself or someone else as a maintainer
            """
            await ctx.respond(help_text)

        @devr_group.command(name="status", description="Check the bot status")
        async def status_command(ctx):
            await ctx.respond("discord bot is up.")

        @devr_group.command(name="configure_channel", description="Set this channel for GitHub notifications")
        async def configure_channel(ctx):
            try:
                channel_id = ctx.channel.id
                self.config["notification_channel_id"] = channel_id
                self.save_config()
                await ctx.respond(f"This channel will now receive GitHub notifications.")
            except Exception as e:
                logger.error(f"Channel config error: {str(e)}")
                await ctx.respond("Something went wrong while setting up the channel.")

        self.bot.add_application_command(devr_group)

        @devr_group.command(name="register_maintainer", description="Register a user as a maintainer")
        async def register_maintainer(ctx, user: discord.Member = None):
            try:
                if not user:
                    user = ctx.author

                user_id = str(user.id)

                if user_id not in self.config["maintainers"]:
                    self.config["maintainers"].append(user_id)
                    self.save_config()
                    await ctx.respond(f"{user.mention} is now registered as a maintainer.")
                else:
                    await ctx.respond(f"{user.mention} is already on the maintainer list.")
            except Exception as e:
                logger.error(f"Maintainer registration error: {str(e)}")
                await ctx.respond("Something went wrong while registering the maintainer.")

    async def send_message(self, channel_id, message):
        try:
            try:
                channel_id = int(channel_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid channel ID format: {channel_id}")
                return False

            channel = self.bot.get_channel(channel_id)

            if not channel and self.bot.guilds:
                for guild in self.bot.guilds:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        break

            if channel:
                await channel.send(message)
                logger.info(f"Message sent to channel {channel.name} (ID: {channel_id})")
                return True
            else:
                logger.error(f"Channel with ID {channel_id} not found in any guild")

                if self.bot.guilds:
                    visible_channels = [c for g in self.bot.guilds for c in g.text_channels]
                    logger.info(
                        f"Bot can see {len(visible_channels)} text channels across {len(self.bot.guilds)} guilds")

                    for i, ch in enumerate(visible_channels[:5]):  # List first 5 channels
                        logger.info(f"Visible channel {i+1}: {ch.name} (ID: {ch.id})")
                return False
        except Exception as e:
            logger.error(f"Message sending error: {str(e)}")
            return False

    async def notify_github_event(self, event_type, data):
        """Process a pending GitHub event notification"""
        if not self.config.get("notification_channel_id"):
            logger.warning("No notification channel configured")
            return False

        if data is None:
            logger.error("No data provided for notification")
            return False

        channel_id = self.config["notification_channel_id"]
        maintainer_mentions = " ".join([f"<@{user_id}>" for user_id in self.config.get("maintainers", [])])

        try:
            if event_type == "issue_created":
                repository = data.get('repository', 'unknown')
                title = data.get('title', 'No title')
                body_text = data.get('body', 'No description provided')
                body_text = body_text if body_text else 'No description provided'
                user_dict = data.get('user', {}) or {}  # Handle None case
                user_login = user_dict.get('login', 'Unknown')
                html_url = data.get('html_url', 'No link provided')

                message = (
                    f"**New Issue Created in {repository}**\n\n"
                    f"**Title:** {title}\n"
                    f"**Description:** {body_text[:500]}...\n"
                    f"**Created by:** {user_login}\n"
                    f"**Link:** {html_url}\n\n"
                )

                if maintainer_mentions:
                    message += f"cc: {maintainer_mentions}"

                return await self.send_message(channel_id, message)

            elif event_type == "pr_created":
                repository = data.get('repository', 'unknown')
                title = data.get('title', 'No title')
                body_text = data.get('body', 'No description provided')
                body_text = body_text if body_text else 'No description provided'
                user_dict = data.get('user', {}) or {}  # Handle None case
                user_login = user_dict.get('login', 'Unknown')
                html_url = data.get('html_url', 'No link provided')

                message = (
                    f"**New Pull Request in {repository}**\n\n"
                    f"**Title:** {title}\n"
                    f"**Description:** {body_text[:500]}...\n"
                    f"**Created by:** {user_login}\n"
                    f"**Link:** {html_url}\n\n"
                )

                if maintainer_mentions:
                    message += f"cc: {maintainer_mentions}"

                return await self.send_message(channel_id, message)

            else:
                logger.warning(f"Unknown event type: {event_type}")
                return False

        except Exception as e:
            logger.error(f"GitHub notification error: {str(e)}")
            return False

    async def process_event(self, event):
        """Process events from the event bus and send appropriate notifications"""
        try:
            channel_id = self.config.get("notification_channel_id")
            logger.info(f"Attempting to send notification to channel ID: {channel_id}")
            if not channel_id:
                logger.warning("No notification channel configured")
                return False

            maintainer_mentions = " ".join([f"<@{user_id}>" for user_id in self.config.get("maintainers", [])])

            event_type = event.event_type.value

            if event_type == EventType.ISSUE_CREATED.value:
                message = (
                    f"**New Issue Created**\n\n"
                    f"**Title:** {event.title}\n"
                    f"**Description:** {event.body[:500] if event.body else 'No description provided'}...\n"
                    f"**Created by:** {event.actor_name}\n"
                    f"**Link:** {event.url}\n\n"
                )

                if maintainer_mentions:
                    message += f"cc: {maintainer_mentions}"

                await self.send_message(channel_id, message)
                logger.info(f"Sent notification for issue #{event.issue_number}")
                return True

            elif event_type == EventType.PR_CREATED.value:
                message = (
                    f"**New Pull Request**\n\n"
                    f"**Title:** {event.title}\n"
                    f"**Description:** {event.body[:500] if event.body else 'No description provided'}...\n"
                    f"**Created by:** {event.actor_name}\n"
                    f"**Link:** {event.url}\n\n"
                )

                if maintainer_mentions:
                    message += f"cc: {maintainer_mentions}"

                await self.send_message(channel_id, message)
                logger.info(f"Sent notification for PR #{event.pr_number}")
                return True

            else:
                logger.info(f"Event type {event_type} not configured for Discord notifications")
                return False

        except Exception as e:
            logger.error(f"Error processing event in Discord bot: {str(e)}")
            return False

    def run(self):
        if self.token:
            try:
                self.bot.run(self.token)
            except Exception as e:
                logger.error(f"Bot startup failed: {str(e)}")
        else:
            logger.error("Discord Token not provided.")
