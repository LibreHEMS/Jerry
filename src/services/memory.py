"""
Conversation memory management for Jerry AI.

This module handles conversation memory, context tracking,
and conversation summarization for long-term interactions.
"""

from datetime import datetime
from datetime import timedelta
from typing import Any
from uuid import UUID

from ..data.models import MessageRole
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """Manages conversation memory and context for Jerry AI."""

    def __init__(
        self,
        max_messages: int = 20,
        summary_threshold: int = 15,
        context_window_hours: int = 24,
    ):
        """Initialize conversation memory manager."""
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        self.context_window_hours = context_window_hours

        # In-memory storage (in production, this would be database-backed)
        self._conversations: dict[UUID, dict[str, Any]] = {}
        self._summaries: dict[UUID, str] = {}
        self._context_cache: dict[UUID, dict[str, Any]] = {}

    def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to conversation memory."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = {
                "messages": [],
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow(),
                "message_count": 0,
            }

        conversation = self._conversations[conversation_id]

        # Add message
        message_data = {
            "role": role.value,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        conversation["messages"].append(message_data)
        conversation["last_updated"] = datetime.utcnow()
        conversation["message_count"] += 1

        # Maintain message limit
        if len(conversation["messages"]) > self.max_messages:
            # Remove oldest messages but keep the summary
            removed_messages = conversation["messages"][: -self.max_messages]
            conversation["messages"] = conversation["messages"][-self.max_messages :]

            # Update summary with removed messages
            self._update_summary_with_removed_messages(
                conversation_id, removed_messages
            )

        logger.debug(f"Added message to conversation {conversation_id}: {role.value}")

    def get_conversation_context(
        self,
        conversation_id: UUID,
        include_summary: bool = True,
        max_messages: int | None = None,
    ) -> dict[str, Any]:
        """Get conversation context including messages and summary."""
        if conversation_id not in self._conversations:
            return {"messages": [], "summary": "", "context": {}, "message_count": 0}

        conversation = self._conversations[conversation_id]
        messages = conversation["messages"]

        # Limit messages if requested
        if max_messages and len(messages) > max_messages:
            messages = messages[-max_messages:]

        # Get summary
        summary = ""
        if include_summary and conversation_id in self._summaries:
            summary = self._summaries[conversation_id]

        # Get cached context
        context = self._context_cache.get(conversation_id, {})

        return {
            "messages": messages,
            "summary": summary,
            "context": context,
            "message_count": conversation["message_count"],
            "created_at": conversation["created_at"].isoformat(),
            "last_updated": conversation["last_updated"].isoformat(),
        }

    def get_recent_messages(
        self, conversation_id: UUID, count: int = 10
    ) -> list[dict[str, Any]]:
        """Get the most recent messages from a conversation."""
        if conversation_id not in self._conversations:
            return []

        messages = self._conversations[conversation_id]["messages"]
        return messages[-count:] if len(messages) > count else messages

    def update_conversation_summary(self, conversation_id: UUID, summary: str) -> None:
        """Update the summary for a conversation."""
        self._summaries[conversation_id] = summary
        logger.info(f"Updated summary for conversation {conversation_id}")

    def get_conversation_summary(self, conversation_id: UUID) -> str | None:
        """Get the summary for a conversation."""
        return self._summaries.get(conversation_id)

    def should_summarize(self, conversation_id: UUID) -> bool:
        """Check if a conversation should be summarized."""
        if conversation_id not in self._conversations:
            return False

        conversation = self._conversations[conversation_id]
        message_count = len(conversation["messages"])

        return message_count >= self.summary_threshold

    def extract_user_context(self, conversation_id: UUID) -> dict[str, Any]:
        """Extract user context information from conversation."""
        if conversation_id not in self._conversations:
            return {}

        # Check cache first
        if conversation_id in self._context_cache:
            cache_time = self._context_cache[conversation_id].get("cached_at")
            if cache_time:
                cache_datetime = datetime.fromisoformat(cache_time)
                if datetime.utcnow() - cache_datetime < timedelta(hours=1):
                    return self._context_cache[conversation_id].get("context", {})

        # Extract context from messages
        conversation = self._conversations[conversation_id]
        messages = conversation["messages"]

        context = self._analyze_conversation_for_context(messages)

        # Cache the context
        self._context_cache[conversation_id] = {
            "context": context,
            "cached_at": datetime.utcnow().isoformat(),
        }

        return context

    def _analyze_conversation_for_context(
        self, messages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze conversation messages to extract user context."""
        context = {
            "topics": [],
            "location": None,
            "system_details": {},
            "preferences": [],
            "urgency": "normal",
            "expertise_level": "beginner",
        }

        # Combine all message content for analysis
        all_content = " ".join(
            [msg["content"] for msg in messages if msg["role"] in ["user", "assistant"]]
        )
        content_lower = all_content.lower()

        # Extract location information
        australian_locations = {
            "nsw": "New South Wales",
            "vic": "Victoria",
            "qld": "Queensland",
            "wa": "Western Australia",
            "sa": "South Australia",
            "tas": "Tasmania",
            "act": "Australian Capital Territory",
            "nt": "Northern Territory",
            "sydney": "NSW",
            "melbourne": "VIC",
            "brisbane": "QLD",
            "perth": "WA",
            "adelaide": "SA",
            "hobart": "TAS",
            "canberra": "ACT",
            "darwin": "NT",
        }

        for location_key, location_name in australian_locations.items():
            if location_key in content_lower:
                context["location"] = location_name
                break

        # Extract topics discussed
        topic_keywords = {
            "solar": ["solar", "panel", "pv", "photovoltaic", "inverter"],
            "battery": ["battery", "storage", "powerwall", "backup", "blackout"],
            "automation": ["automation", "smart", "control", "timer", "load"],
            "hot_water": ["hot water", "heat pump", "electric", "gas"],
            "pool": ["pool", "spa", "swimming", "heating", "pump"],
            "ev": ["electric vehicle", "ev", "car", "charging", "tesla"],
            "tariffs": ["tariff", "bill", "cost", "rate", "feed-in"],
            "rebates": ["rebate", "incentive", "subsidy", "grant"],
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                context["topics"].append(topic)

        # Extract system details
        if "kw" in content_lower or "kilowatt" in content_lower:
            # Try to extract system size
            import re

            size_matches = re.findall(r"(\d+(?:\.\d+)?)\s*kw", content_lower)
            if size_matches:
                context["system_details"]["solar_size_kw"] = size_matches[-1]

        if "battery" in content_lower:
            battery_matches = re.findall(r"(\d+(?:\.\d+)?)\s*kwh", content_lower)
            if battery_matches:
                context["system_details"]["battery_size_kwh"] = battery_matches[-1]

        # Detect urgency
        urgency_keywords = [
            "urgent",
            "asap",
            "quickly",
            "emergency",
            "broken",
            "not working",
        ]
        if any(keyword in content_lower for keyword in urgency_keywords):
            context["urgency"] = "high"

        # Detect expertise level
        expert_keywords = [
            "technical",
            "specifications",
            "inverter type",
            "mppt",
            "dc optimizers",
        ]
        beginner_keywords = [
            "new to solar",
            "don't know much",
            "beginner",
            "explain simply",
        ]

        if any(keyword in content_lower for keyword in expert_keywords):
            context["expertise_level"] = "advanced"
        elif any(keyword in content_lower for keyword in beginner_keywords):
            context["expertise_level"] = "beginner"
        else:
            context["expertise_level"] = "intermediate"

        return context

    def _update_summary_with_removed_messages(
        self, conversation_id: UUID, removed_messages: list[dict[str, Any]]
    ) -> None:
        """Update conversation summary when messages are removed."""
        if not removed_messages:
            return

        # Get existing summary
        existing_summary = self._summaries.get(conversation_id, "")

        # Create a simple summary of removed messages
        user_messages = [msg for msg in removed_messages if msg["role"] == "user"]

        removed_summary = (
            f"Previous discussion covered {len(user_messages)} user questions "
        )

        # Extract key topics from removed messages
        topics = set()
        for msg in removed_messages:
            content_lower = msg["content"].lower()
            if "solar" in content_lower:
                topics.add("solar")
            if "battery" in content_lower:
                topics.add("battery")
            if "automation" in content_lower:
                topics.add("automation")

        if topics:
            removed_summary += f"about {', '.join(topics)}. "

        # Combine with existing summary
        if existing_summary:
            combined_summary = f"{existing_summary}\n\n{removed_summary}"
        else:
            combined_summary = removed_summary

        self._summaries[conversation_id] = combined_summary

    def clear_conversation(self, conversation_id: UUID) -> None:
        """Clear all data for a conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
        if conversation_id in self._summaries:
            del self._summaries[conversation_id]
        if conversation_id in self._context_cache:
            del self._context_cache[conversation_id]

        logger.info(f"Cleared conversation data for {conversation_id}")

    def get_conversation_stats(self, conversation_id: UUID) -> dict[str, Any]:
        """Get statistics about a conversation."""
        if conversation_id not in self._conversations:
            return {}

        conversation = self._conversations[conversation_id]
        messages = conversation["messages"]

        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]

        # Calculate duration
        if messages:
            start_time = datetime.fromisoformat(messages[0]["timestamp"])
            end_time = datetime.fromisoformat(messages[-1]["timestamp"])
            duration_minutes = (end_time - start_time).total_seconds() / 60
        else:
            duration_minutes = 0

        return {
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "duration_minutes": round(duration_minutes, 2),
            "topics_discussed": len(
                self.extract_user_context(conversation_id).get("topics", [])
            ),
            "has_summary": conversation_id in self._summaries,
        }

    def cleanup_old_conversations(self, max_age_days: int = 30) -> int:
        """Clean up conversations older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0

        conversations_to_remove = []
        for conv_id, conversation in self._conversations.items():
            if conversation["last_updated"] < cutoff_date:
                conversations_to_remove.append(conv_id)

        for conv_id in conversations_to_remove:
            self.clear_conversation(conv_id)
            cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} old conversations")
        return cleaned_count


# Global memory manager instance
_memory_manager: ConversationMemory | None = None


def get_memory_manager() -> ConversationMemory:
    """Get the global conversation memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ConversationMemory()
    return _memory_manager


def create_memory_manager(
    max_messages: int = 20, summary_threshold: int = 15, context_window_hours: int = 24
) -> ConversationMemory:
    """Create a conversation memory manager with custom settings."""
    return ConversationMemory(
        max_messages=max_messages,
        summary_threshold=summary_threshold,
        context_window_hours=context_window_hours,
    )
