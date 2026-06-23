"""Shared TCP protocol helpers for the face expression game.

The socket uses a simple line-based protocol:

    COMMAND|value_1|value_2\n

Using one newline per message is important because TCP is a stream. Without a
clear delimiter, two messages can arrive joined together or split into chunks.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass


HOST = "127.0.0.1"
PORT = 5050
ENCODING = "utf-8"
SEPARATOR = "|"
GAME_DURATION_SECONDS = 60
NEXT_TARGET_DELAY_SECONDS = 1.0


@dataclass(frozen=True)
class Message:
    """Parsed protocol message."""

    command: str
    parts: list[str]


def encode_message(command: str, *parts: object) -> bytes:
    """Convert a command and payload into bytes ready for socket.sendall()."""
    values = [command, *(str(part) for part in parts)]
    return (SEPARATOR.join(values) + "\n").encode(ENCODING)


def decode_message(line: str) -> Message:
    """Parse one received line into a Message object."""
    values = line.strip().split(SEPARATOR)
    command = values[0] if values else ""
    return Message(command=command, parts=values[1:])


def send_message(sock: socket.socket, command: str, *parts: object) -> None:
    """Send one complete protocol message."""
    sock.sendall(encode_message(command, *parts))
