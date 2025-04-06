import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DevrAIDiscordBot:
    """Discord bot implementation for Devr.AI"""

    def __init__(self):
        """Initialize the Discord bot"""
        self.token = os.getenv("DISCORD_BOT_TOKEN")

        if not self.token:
            logger.warning("Discord bot token not provided. Bot will not be able to connect.")

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.setup_event_handlers()
        self.register_commands()

    def setup_event_handlers(self):
        """Set up event handlers for Discord events"""
        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot logged in as {self.bot.user}")

        @self.bot.event
        async def on_message(message):
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return

            # Process commands
            await self.bot.process_commands(message)

            # Handle regular messages (if not a command)
            if not message.content.startswith(self.bot.command_prefix):
                logger.debug(f"Message in {message.channel}: {message.content}")
                # TODO: Process message through event bus

        @self.bot.event
        async def on_member_join(member):
            logger.info(f"New member joined: {member.name}#{member.discriminator}")
            # TODO: Send welcome message to new user

    def register_commands(self):
        """Register Discord bot commands"""
        @self.bot.command(name="help")
        async def help_command(ctx):
            """Show help for bot commands"""
            help_text = """
            **Devr.AI Bot Commands**
            
            `/help` - Show this help message
            `/status` - Check bot status
            `/link` - Link your Discord account to GitHub
            """
            await ctx.send(help_text)

        @self.bot.command(name="status")
        async def status_command(ctx):
            """Check the status of the bot"""
            await ctx.send("Devr.AI bot is up and running!")

    async def send_message(self, channel_id, message):
        """Send a message to a specific channel"""
        try:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                await channel.send(message)
                return True
            else:
                logger.error(f"Channel with ID {channel_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error sending message to Discord: {str(e)}")
            return False

    def run(self):
        """Run the Discord bot"""
        if self.token:
            try:
                self.bot.run(self.token)
            except Exception as e:
                logger.error(f"Failed to start Discord bot: {str(e)}")
        else:
            logger.error("Cannot start Discord bot: Token not provided")
