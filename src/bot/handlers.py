"""
Discord event handlers for Jerry AI assistant.

This module handles Discord events like direct messages,
mentions, and other bot interactions.
"""

import logging
import re

import discord
from discord.ext import commands

from ..data.models import Conversation
from ..data.models import User
from ..utils.config import Config

logger = logging.getLogger(__name__)


class JerryHandlers(commands.Cog):
    """Jerry AI event handlers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages."""
        # Ignore messages from bots (including self)
        if message.author.bot:
            return

        # Handle direct messages
        if isinstance(message.channel, discord.DMChannel):
            await self._handle_direct_message(message)
            return

        # Handle mentions in guild channels
        if self.bot.user in message.mentions:
            await self._handle_mention(message)
            return

        # Process commands
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Welcome new members to the server."""
        if not self.config.discord.welcome_enabled:
            return

        # Send welcome message in DM
        try:
            embed = discord.Embed(
                title="🌟 Welcome to the Community!",
                description=(
                    f"G'day {member.display_name}! 👋\n\n"
                    "Welcome to our Australian renewable energy community! "
                    "I'm Jerry, your friendly AI advisor here to help with "
                    "solar panels, batteries, home automation, and energy savings.\n\n"
                    "Feel free to ask me questions anytime using `/jerry` "
                    "or send me a direct message!"
                ),
                color=discord.Color.gold(),
            )

            embed.add_field(
                name="🔋 What I can help with:",
                value=(
                    "• Solar system sizing and recommendations\n"
                    "• Battery storage advice\n"
                    "• Home automation integration\n"
                    "• Energy efficiency tips\n"
                    "• Australian energy market insights"
                ),
                inline=False,
            )

            embed.set_footer(
                text="Powered by self-hosted AI • Your privacy is protected"
            )

            await member.send(embed=embed)
            logger.info(f"Sent welcome message to {member}")

        except discord.Forbidden:
            logger.warning(f"Cannot send DM to {member} - DMs disabled")
        except Exception as e:
            logger.error(f"Error sending welcome message to {member}: {e}")

    async def _handle_direct_message(self, message: discord.Message) -> None:
        """Handle direct messages to Jerry."""
        try:
            # Show typing indicator
            async with message.channel.typing():
                # Process message through agent service if available
                response_content = await self._process_message_with_agent(
                    message.author, message.channel.id, message.content, is_dm=True
                )

                # Send response
                await message.reply(response_content)

                logger.info(
                    f"Processed DM from {message.author}: {message.content[:50]}..."
                )

        except Exception as e:
            logger.error(f"Error handling DM from {message.author}: {e}", exc_info=True)
            await message.reply(
                "🚫 Sorry mate, I'm having a bit of trouble right now. "
                "Please try again in a moment!"
            )

    async def _handle_mention(self, message: discord.Message) -> None:
        """Handle mentions of Jerry in guild channels."""
        try:
            # Extract the message content without the mention
            content = message.content
            mention_pattern = f"<@!?{self.bot.user.id}>"
            content = re.sub(mention_pattern, "", content).strip()

            if not content:
                # Just mentioned without a question
                await message.reply(
                    "G'day! 👋 You can ask me questions about renewable energy, "
                    "solar panels, batteries, or home automation. What would you like to know?"
                )
                return

            # Show typing indicator
            async with message.channel.typing():
                # Process message through agent service if available
                response_content = await self._process_message_with_agent(
                    message.author,
                    message.channel.id,
                    content,
                    is_dm=False,
                    guild=message.guild,
                )

                # Send response
                await message.reply(response_content)

                logger.info(
                    f"Processed mention from {message.author} in {message.guild}: "
                    f"{content[:50]}..."
                )

        except Exception as e:
            logger.error(
                f"Error handling mention from {message.author}: {e}", exc_info=True
            )
            await message.reply(
                "🚫 Sorry mate, I'm having a bit of trouble right now. "
                "Please try again in a moment!"
            )

    async def _process_message_with_agent(
        self,
        author: discord.User,
        channel_id: int,
        content: str,
        is_dm: bool = False,
        guild: discord.Guild | None = None,
    ) -> str:
        """Process a message through the agent service if available."""
        # Check if bot has agent service available
        if hasattr(self.bot, "model_registry") and self.bot.model_registry:
            try:
                # Get model service to check if agent service could work
                model_service = self.bot.model_registry.get()
                health = await model_service.health_check()

                if health.healthy and health.model_loaded:
                    # Create user and conversation objects
                    user = await self._get_or_create_user(author)
                    await self._get_or_create_conversation(user, str(channel_id))

                    # For now, use a simple local agent processing
                    # In a full implementation, this would call the agent service
                    return await self._process_with_local_agent(
                        content, author, is_dm, guild
                    )

            except Exception as e:
                logger.warning(f"Agent service not available: {e}")

        # Fallback to simple responses
        return await self._generate_fallback_response(content, author, is_dm, guild)

    async def _process_with_local_agent(
        self,
        content: str,
        author: discord.User,
        is_dm: bool,
        guild: discord.Guild | None,
    ) -> str:
        """Process message with a simplified local agent."""
        # This is a simplified version until full agent integration
        # In the complete implementation, this would use the AgentService

        content_lower = content.lower()

        # Greeting detection
        greeting_keywords = [
            "hello",
            "hi",
            "hey",
            "g'day",
            "gday",
            "morning",
            "afternoon",
        ]
        if any(keyword in content_lower for keyword in greeting_keywords):
            return self._get_greeting_response(author, is_dm, guild)

        # Topic-specific responses
        if any(keyword in content_lower for keyword in ["solar", "panel", "pv"]):
            return self._get_solar_response(content, author)

        if any(
            keyword in content_lower for keyword in ["battery", "storage", "backup"]
        ):
            return self._get_battery_response(content, author)

        if any(
            keyword in content_lower for keyword in ["automation", "smart", "control"]
        ):
            return self._get_automation_response(content, author)

        # General response
        return self._get_general_response(content, author, is_dm, guild)

    def _get_greeting_response(
        self, author: discord.User, is_dm: bool, guild: discord.Guild | None
    ) -> str:
        """Get a greeting response."""
        if is_dm:
            return (
                f"G'day {author.display_name}! 👋\n\n"
                "Great to chat with you privately! I'm Jerry, your friendly "
                "Australian renewable energy advisor. I'm here to help you with "
                "anything related to solar panels, batteries, home automation, "
                "and energy savings.\n\n"
                "My AI brain is now powered by a local model, so your privacy "
                "is completely protected. What would you like to know about?"
            )
        guild_name = guild.name if guild else "this server"
        return (
            f"G'day {author.display_name}! 👋\n\n"
            f"Thanks for reaching out here in {guild_name}! I'm Jerry, "
            "your renewable energy advisor. I'm now running on a self-hosted "
            "AI system, which means faster responses and better privacy.\n\n"
            "What can I help you with today? Solar, batteries, or home automation?"
        )

    def _get_solar_response(self, content: str, author: discord.User) -> str:
        """Get a solar-specific response."""
        return (
            f"🌞 **Solar Panel Advice for {author.display_name}**\n\n"
            "Solar is a fantastic investment in Australia! With my upgraded AI brain, "
            "I can now provide more detailed, personalized advice based on your "
            "specific situation.\n\n"
            "To give you the best recommendations, I'd love to know:\n"
            "• What state are you in?\n"
            "• What's your approximate quarterly electricity bill?\n"
            "• Do you have a north-facing roof?\n"
            "• Are you considering battery storage too?\n\n"
            "Feel free to share as much detail as you're comfortable with!"
        )

    def _get_battery_response(self, content: str, author: discord.User) -> str:
        """Get a battery-specific response."""
        return (
            f"🔋 **Battery Storage Advice for {author.display_name}**\n\n"
            "Battery storage is becoming increasingly popular in Australia, and "
            "with my enhanced AI capabilities, I can help you make the right choice!\n\n"
            "Key questions to consider:\n"
            "• Do you already have solar panels?\n"
            "• What's driving your interest - backup power or bill savings?\n"
            "• Have you experienced power outages in your area?\n"
            "• What's your typical daily energy usage?\n\n"
            "Let me know your situation and I'll provide tailored recommendations!"
        )

    def _get_automation_response(self, content: str, author: discord.User) -> str:
        """Get an automation-specific response."""
        return (
            f"🏠 **Home Automation Advice for {author.display_name}**\n\n"
            "Smart energy management can really optimize your renewable energy setup! "
            "With my upgraded AI, I can help you design an automation strategy.\n\n"
            "What aspects interest you most:\n"
            "• Smart load management (shifting usage to solar hours)?\n"
            "• Hot water and pool heating automation?\n"
            "• EV charging optimization?\n"
            "• Whole-home energy monitoring?\n\n"
            "Tell me about your current setup and goals!"
        )

    def _get_general_response(
        self,
        content: str,
        author: discord.User,
        is_dm: bool,
        guild: discord.Guild | None,
    ) -> str:
        """Get a general response."""
        return (
            f"Thanks for your question, {author.display_name}! 🤔\n\n"
            f"You asked: *{content[:100]}{'...' if len(content) > 100 else ''}*\n\n"
            "I'm Jerry, your renewable energy advisor, now powered by a fully "
            "self-hosted AI system! This means better privacy, faster responses, "
            "and more detailed advice.\n\n"
            "I specialize in solar panels, batteries, home automation, and the "
            "Australian energy market. Could you rephrase your question or let me "
            "know which area you'd like help with?"
        )

    async def _generate_fallback_response(
        self,
        content: str,
        author: discord.User,
        is_dm: bool,
        guild: discord.Guild | None,
    ) -> str:
        """Generate a fallback response when agent service is unavailable."""
        return (
            f"G'day {author.display_name}! 👋\n\n"
            "I'm Jerry, your renewable energy advisor! My AI brain is currently "
            "being upgraded to a fully self-hosted system for better privacy and "
            "performance.\n\n"
            "I can still help with general questions about solar panels, batteries, "
            "and home automation. What would you like to know?"
        )

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
    await bot.add_cog(JerryHandlers(bot))
    logger.info("JerryHandlers cog loaded successfully")
