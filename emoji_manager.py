"""Emoji selection utilities used by the server and client."""

from __future__ import annotations

import random


EMOJI_TO_EXPRESSION = {
    "😀": "smile",
    "😮": "surprise",
    "😐": "neutral",
}

EXPRESSION_TO_EMOJI = {value: key for key, value in EMOJI_TO_EXPRESSION.items()}


class EmojiManager:
    """Pick random target emojis for each round."""

    def __init__(self) -> None:
        self._emojis = list(EMOJI_TO_EXPRESSION.keys())

    def get_random_emoji(self, previous_emoji: str | None = None) -> str:
        """Return a random emoji, avoiding the previous one when possible."""
        choices = self._emojis
        if previous_emoji and len(choices) > 1:
            choices = [emoji for emoji in choices if emoji != previous_emoji]

        return random.choice(choices)


def get_expression_for_emoji(emoji: str) -> str:
    """Translate target emoji into the expression label used by the detector."""
    return EMOJI_TO_EXPRESSION.get(emoji, "neutral")
