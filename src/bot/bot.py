"""
Discord bot client setup for Jerry AI assistant.

This module initializes the Discord bot client and sets up
the core bot functionality for Jerry.
"""

import asyncio
import logging

import discord
from discord.ext import commands

from ..services.local_model_service import LocalModelService
from ..services.model_service import ModelServiceRegistry
from ..utils.config import Config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class JerryBot(commands.Bot):
    """Jerry AI Discord bot client."""

    def __init__(self, config: Config):
        """Initialize Jerry bot with configuration."""
        self.config = config
        self.model_registry = ModelServiceRegistry()

        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.direct_messages = True

        # Initialize bot with command prefix
        super().__init__(
            command_prefix=config.discord.command_prefix,
            intents=intents,
            help_command=None,  # We'll implement custom help
        )

    async def setup_hook(self) -> None:
        """Setup hook called when bot is starting up."""
        logger.info("Jerry bot is starting up...")

        # Initialize model services
        try:
            await self._setup_model_services()
        except Exception as e:
            logger.error(f"Failed to setup model services: {e}", exc_info=True)
            # Continue without model services for now

        # Load command extensions
        try:
            await self.load_extension("src.bot.commands")
            await self.load_extension("src.bot.handlers")
            logger.info("Successfully loaded bot extensions")
        except Exception as e:
            logger.error(f"Failed to load bot extensions: {e}")
            raise

        # Sync application commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} application commands")
        except Exception as e:
            logger.error(f"Failed to sync application commands: {e}")

    async def _setup_model_services(self) -> None:
        """Setup model services for the bot."""
        logger.info("Setting up model services...")

        try:
            # Create local model service
            local_service = LocalModelService(self.config.model)
            self.model_registry.register("local", local_service, default=True)

            # Load the model
            await local_service.load_model()
            logger.info("Local model service loaded successfully")

        except Exception as e:
            logger.warning(f"Failed to load local model service: {e}")
            # Bot can still function without model service
            # Commands will show appropriate messages

    async def on_ready(self) -> None:
        """Called when the bot has successfully logged in."""
        logger.info(f"Jerry bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching, name="Australian solar systems ☀️"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """Handle bot errors."""
        logger.error(f"Error in {event_method}", exc_info=True)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You don't have permission to use this command, mate!")
            return

        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("🚫 I don't have the required permissions to do that!")
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏰ This command is on cooldown. "
                f"Try again in {error.retry_after:.1f} seconds."
            )
            return

        # Log unexpected errors
        logger.error(
            f"Unexpected command error in {ctx.command}: {error}", exc_info=True
        )
        await ctx.send("🤖 Crikey! Something went wrong. The error has been logged.")

    async def close(self) -> None:
        """Clean shutdown of the bot."""
        logger.info("Jerry bot is shutting down...")

        # Shutdown model services
        try:
            await self.model_registry.shutdown_all()
            logger.info("Model services shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down model services: {e}")

        await super().close()


class BotManager:
    """Manager for the Jerry Discord bot."""

    def __init__(self, config: Config):
        self.config = config
        self.bot: JerryBot | None = None
        self._running = False

    async def start(self) -> None:
        """Start the Discord bot."""
        if self._running:
            logger.warning("Bot is already running")
            return

        logger.info("Starting Jerry Discord bot...")
        self.bot = JerryBot(self.config)

        try:
            self._running = True
            await self.bot.start(self.config.discord.bot_token)
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self._running = False
            raise
        finally:
            if self.bot:
                await self.bot.close()

    async def stop(self) -> None:
        """Stop the Discord bot."""
        if not self._running or not self.bot:
            logger.warning("Bot is not running")
            return

        logger.info("Stopping Jerry Discord bot...")
        await self.bot.close()
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if the bot is currently running."""
        return self._running and self.bot is not None

    @property
    def user(self) -> discord.ClientUser | None:
        """Get the bot user if available."""
        return self.bot.user if self.bot else None


async def create_bot(config: Config) -> JerryBot:
    """Create and configure a Jerry bot instance."""
    setup_logging(config.logging)
    return JerryBot(config)


async def run_bot(config: Config) -> None:
    """Run the Jerry Discord bot."""
    manager = BotManager(config)

    try:
        await manager.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        await manager.stop()


if __name__ == "__main__":
    # This allows running the bot directly for testing
    import os
    import sys

    # Add the parent directory to the path so we can import from src
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    from src.utils.config import load_config

    config = load_config()
    asyncio.run(run_bot(config))
