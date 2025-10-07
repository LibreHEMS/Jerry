"""
Discord command handlers for Jerry AI assistant.

This module contains slash commands and traditional commands
for interacting with Jerry through Discord.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..data.models import Conversation
from ..data.models import Message
from ..data.models import User
from ..utils.config import Config

logger = logging.getLogger(__name__)


class JerryCommands(commands.Cog):
    """Jerry AI command handlers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config

    @app_commands.command(
        name="jerry", description="Ask Jerry a question about renewable energy"
    )
    @app_commands.describe(
        question="Your question about solar, batteries, or home automation"
    )
    async def jerry_command(
        self, interaction: discord.Interaction, question: str
    ) -> None:
        """Main Jerry command for asking questions."""
        await interaction.response.defer(thinking=True)

        try:
            # Create or get user
            user = await self._get_or_create_user(interaction.user)

            # Create or get conversation
            conversation = await self._get_or_create_conversation(
                user, str(interaction.channel_id)
            )

            # Create user message
            Message.create_user_message(conversation.id, question)

            # TODO: Process question with agent service
            # For now, provide a placeholder response
            response_content = (
                f"G'day {interaction.user.display_name}! 👋\n\n"
                f"Thanks for your question: *{question}*\n\n"
                "I'm Jerry, your friendly Australian renewable energy advisor! "
                "I'm currently getting my AI brain updated to help you better. "
                "Once the migration is complete, I'll be able to provide detailed "
                "advice about solar panels, batteries, home automation, and more!\n\n"
                "Stay tuned, mate! ☀️🔋"
            )

            # Create assistant message
            Message.create_assistant_message(
                conversation.id,
                response_content,
                model_used="placeholder",
            )

            # Update conversation stats
            conversation.add_message_stats(0)  # TODO: Add actual token count

            # Send response
            embed = discord.Embed(
                title="🤖 Jerry AI Assistant",
                description=response_content,
                color=discord.Color.green(),
            )
            embed.set_footer(
                text="Powered by self-hosted AI • Australian renewable energy expert"
            )

            await interaction.followup.send(embed=embed)

            logger.info(
                f"Processed jerry command from {interaction.user} "
                f"in {interaction.guild} #{interaction.channel}"
            )

        except Exception as e:
            logger.error(f"Error processing jerry command: {e}", exc_info=True)
            await interaction.followup.send(
                "🚫 Sorry mate, I'm having a bit of trouble right now. "
                "Please try again in a moment!",
                ephemeral=True,
            )

    @app_commands.command(name="jerry-help", description="Get help with Jerry commands")
    async def jerry_help_command(self, interaction: discord.Interaction) -> None:
        """Display help information for Jerry."""
        embed = discord.Embed(
            title="🤖 Jerry AI Assistant - Help",
            description=(
                "G'day! I'm Jerry, your friendly Australian renewable energy advisor. "
                "Here's how to chat with me:"
            ),
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="💬 Ask Questions",
            value=(
                "Use `/jerry <question>` to ask me anything about:\n"
                "• Solar panel systems\n"
                "• Battery storage solutions\n"
                "• Home automation\n"
                "• Energy efficiency\n"
                "• Australian energy markets"
            ),
            inline=False,
        )

        embed.add_field(
            name="📧 Direct Messages",
            value=(
                "You can also send me a direct message for private conversations! "
                "Just start typing and I'll respond."
            ),
            inline=False,
        )

        embed.add_field(
            name="🛡️ Privacy",
            value=(
                "I'm completely self-hosted with no external dependencies. "
                "Your conversations stay secure and private."
            ),
            inline=False,
        )

        embed.set_footer(
            text="Powered by self-hosted AI • Made with ❤️ for the Australian community"
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="jerry-status", description="Check Jerry's status and health"
    )
    async def jerry_status_command(self, interaction: discord.Interaction) -> None:
        """Display Jerry's current status."""
        embed = discord.Embed(title="🤖 Jerry Status", color=discord.Color.green())

        # Bot status
        embed.add_field(name="🟢 Bot Status", value="Online and ready!", inline=True)

        # Latency
        latency_ms = round(self.bot.latency * 1000, 1)
        embed.add_field(name="⚡ Latency", value=f"{latency_ms}ms", inline=True)

        # Guilds
        guild_count = len(self.bot.guilds)
        embed.add_field(name="🏠 Servers", value=f"{guild_count} servers", inline=True)

        # TODO: Add model service status when available
        embed.add_field(
            name="🧠 AI Model", value="Migrating to self-hosted...", inline=True
        )

        embed.add_field(
            name="📚 Knowledge Base",
            value="Loading Australian energy data...",
            inline=True,
        )

        embed.add_field(name="🔧 System", value="All systems operational", inline=True)

        embed.set_footer(text="Self-hosted AI • Zero external dependencies")

        await interaction.response.send_message(embed=embed)

    @commands.command(name="ping")
    async def ping_command(self, ctx: commands.Context) -> None:
        """Simple ping command for testing."""
        latency_ms = round(self.bot.latency * 1000, 1)
        await ctx.send(f"🏓 Pong! Latency: {latency_ms}ms")

    async def _get_or_create_user(self, discord_user: discord.User) -> User:
        """Get or create a User instance from Discord user."""
        # TODO: Implement database storage/retrieval
        # For now, create a new User instance
        from datetime import datetime

        return User(
            discord_id=str(discord_user.id),
            username=discord_user.name,
            display_name=discord_user.display_name or discord_user.name,
            first_interaction=datetime.utcnow(),
            last_interaction=datetime.utcnow(),
        )

    async def _get_or_create_conversation(
        self, user: User, channel_id: str
    ) -> Conversation:
        """Get or create a Conversation instance."""
        # TODO: Implement database storage/retrieval
        # For now, create a new Conversation instance
        return Conversation.create_new(user.discord_id, channel_id)


async def setup(bot: commands.Bot) -> None:
    """Setup function for loading this cog."""
    await bot.add_cog(JerryCommands(bot))
    logger.info("JerryCommands cog loaded successfully")
