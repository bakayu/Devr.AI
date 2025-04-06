#!/usr/bin/env python
"""Script to run the Discord bot independently for testing"""

from bot import DevrAIDiscordBot
import logging

def setup_logging():
    """Set up basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )


def main():
    setup_logging()

    # Create and run the Discord bot
    discord_bot = DevrAIDiscordBot()
    discord_bot.run()


if __name__ == "__main__":
    main()
