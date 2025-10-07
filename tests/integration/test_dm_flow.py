"""Integration tests for Discord DM conversation flow."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestDMFlowIntegration:
    """Test Discord DM conversation flow integration."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot."""
        bot = MagicMock()
        bot.user = MagicMock()
        bot.user.id = 12345
        return bot

    @pytest.fixture
    def mock_dm_message(self):
        """Create a mock Discord DM message."""
        message = MagicMock()
        message.author = MagicMock()
        message.author.id = "user123"
        message.author.display_name = "TestUser"
        message.author.bot = False
        message.channel = MagicMock()
        message.channel.type.name = "private"
        message.content = "Hello Jerry, can you help me with solar panels?"
        message.reply = AsyncMock()
        return message

    @pytest.mark.asyncio
    async def test_dm_message_handling(self, mock_bot, mock_dm_message):
        """Test that DM messages are processed correctly."""

        with patch("src.bot.handlers.agent_service") as mock_agent:
            mock_agent.chat = AsyncMock(
                return_value={
                    "message": "I'd be happy to help you with solar panels! What would you like to know?",
                    "conversation_id": "dm_conv123",
                    "response_time_ms": 200,
                    "tokens_used": 35,
                    "sources_used": ["solar_guide.pdf"],
                    "tools_used": [],
                    "cached": False,
                }
            )

            try:
                from src.bot.handlers import handle_dm_message

                await handle_dm_message(mock_dm_message)

                # Verify message was processed and reply sent
                mock_agent.chat.assert_called_once()
                mock_dm_message.reply.assert_called_once()

                # Verify conversation context was maintained
                call_args = mock_agent.chat.call_args[1]
                assert call_args["user_id"] == "user123"
                assert call_args["channel_id"] == mock_dm_message.channel.id

            except ImportError:
                pytest.fail("DM handler not implemented yet - this is expected in TDD")

    @pytest.mark.asyncio
    async def test_dm_conversation_context(self, mock_bot, mock_dm_message):
        """Test that DM conversations maintain context across messages."""

        with patch("src.bot.handlers.agent_service") as mock_agent:
            # First message
            mock_agent.chat = AsyncMock(
                return_value={
                    "message": "Solar panels convert sunlight to electricity.",
                    "conversation_id": "dm_conv123",
                    "response_time_ms": 180,
                    "tokens_used": 30,
                    "sources_used": [],
                    "tools_used": [],
                    "cached": False,
                }
            )

            try:
                from src.bot.handlers import handle_dm_message

                # First message
                mock_dm_message.content = "What are solar panels?"
                await handle_dm_message(mock_dm_message)

                # Second message in same conversation
                mock_dm_message.content = "How much do they cost?"
                await handle_dm_message(mock_dm_message)

                # Should have been called twice
                assert mock_agent.chat.call_count == 2

                # Both calls should reference the same user/channel
                calls = mock_agent.chat.call_args_list
                assert calls[0][1]["user_id"] == calls[1][1]["user_id"]
                assert calls[0][1]["channel_id"] == calls[1][1]["channel_id"]

            except ImportError:
                pytest.fail("DM handler not implemented yet - this is expected in TDD")

    @pytest.mark.asyncio
    async def test_dm_typing_indicator(self, mock_bot, mock_dm_message):
        """Test that typing indicator is shown during processing."""

        with patch("src.bot.handlers.agent_service") as mock_agent:
            mock_agent.chat = AsyncMock(
                return_value={
                    "message": "Response",
                    "conversation_id": "conv123",
                    "response_time_ms": 1000,
                    "tokens_used": 20,
                    "sources_used": [],
                    "tools_used": [],
                    "cached": False,
                }
            )

            # Add typing method to channel mock
            mock_dm_message.channel.typing = AsyncMock()

            try:
                from src.bot.handlers import handle_dm_message

                await handle_dm_message(mock_dm_message)

                # Should show typing while processing
                mock_dm_message.channel.typing.assert_called()

            except ImportError:
                pytest.fail("DM handler not implemented yet - this is expected in TDD")

    @pytest.mark.asyncio
    async def test_dm_ignore_bot_messages(self, mock_bot, mock_dm_message):
        """Test that bot messages are ignored in DMs."""

        # Set message author as a bot
        mock_dm_message.author.bot = True

        with patch("src.bot.handlers.agent_service") as mock_agent:
            mock_agent.chat = AsyncMock()

            try:
                from src.bot.handlers import handle_dm_message

                await handle_dm_message(mock_dm_message)

                # Should not call agent service for bot messages
                mock_agent.chat.assert_not_called()
                mock_dm_message.reply.assert_not_called()

            except ImportError:
                pytest.fail("DM handler not implemented yet - this is expected in TDD")


# These tests should initially FAIL since DM handlers don't exist yet
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
