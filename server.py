"""TCP game server with a simple Tkinter dashboard."""

from __future__ import annotations

import socket
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from emoji_manager import EmojiManager
from protocol import (
    GAME_DURATION_SECONDS,
    HOST,
    NEXT_TARGET_DELAY_SECONDS,
    PORT,
    decode_message,
    send_message,
)

class FaceFilterGameServer:
    """Manage client connection, game state, and server GUI."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Face Filter Game Server")
        self.root.geometry("420x360")
        self.root.resizable(False, False)

        self.emoji_manager = EmojiManager()
        self.server_socket: socket.socket | None = None
        self.client_socket: socket.socket | None = None
        self.client_file = None

        self.lock = threading.Lock()
        self.send_lock = threading.Lock()

        self.client_connected = False
        self.game_preparing = False
        self.game_active = False
        self.waiting_next_target = False
        self.score = 0
        self.time_left = GAME_DURATION_SECONDS
        self.active_emoji = "-"
        self.status = "Waiting Client"
        self.round_id = 0

        self.client_status_var = tk.StringVar(value="Disconnected")
        self.time_var = tk.StringVar(value=str(GAME_DURATION_SECONDS))
        self.emoji_var = tk.StringVar(value="-")
        self.score_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value="Waiting Client")

        self._build_ui()
        self._start_socket_server()

    def _build_ui(self) -> None:
        title = ttk.Label(
            self.root,
            text="Face Filter Game Server",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(24, 18))

        content = ttk.Frame(self.root, padding=16)
        content.pack(fill="x")

        self._add_info_row(content, "Client Status", self.client_status_var, 0)
        self._add_info_row(content, "Waktu", self.time_var, 1)
        self._add_info_row(content, "Emoji Aktif", self.emoji_var, 2)
        self._add_info_row(content, "Skor", self.score_var, 3)
        self._add_info_row(content, "Status", self.status_var, 4)

        self.start_button = ttk.Button(
            self.root,
            text="START GAME",
            command=self.start_game,
            state="disabled",
        )
        self.start_button.pack(pady=24, ipadx=24, ipady=8)

    @staticmethod
    def _add_info_row(parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=f"{label} :", font=("Segoe UI", 11)).grid(
            row=row,
            column=0,
            sticky="w",
            pady=6,
        )
        ttk.Label(parent, textvariable=variable, font=("Segoe UI", 11, "bold")).grid(
            row=row,
            column=1,
            sticky="w",
            padx=(16, 0),
            pady=6,
        )

    def _start_socket_server(self) -> None:
        thread = threading.Thread(target=self._accept_client, daemon=True)
        thread.start()

    def _accept_client(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(1)

        print(f"Server listening on {HOST}:{PORT}")
        client_socket, address = self.server_socket.accept()

        with self.lock:
            self.client_socket = client_socket
            self.client_file = client_socket.makefile("r", encoding="utf-8")
            self.client_connected = True
            self.status = "Connected"

        print(f"Client connected from {address}")
        self.root.after(0, self._refresh_ui)
        self.root.after(0, lambda: self.start_button.config(state="normal"))

        self._receive_client_messages()

    def _receive_client_messages(self) -> None:
        while self.client_connected and self.client_file:
            line = self.client_file.readline()
            if not line:
                break

            message = decode_message(line)
            if message.command == "MATCH" and message.parts:
                self._handle_match(message.parts[0])
            elif message.command == "NO_MATCH" and message.parts:
                self._handle_no_match(message.parts[0])
            elif message.command == "CAMERA_READY":
                self._handle_camera_ready()
            elif message.command == "CAMERA_ERROR":
                self._handle_camera_error()

        with self.lock:
            self.client_connected = False
            self.game_preparing = False
            self.game_active = False
            self.waiting_next_target = False
            self.status = "Disconnected"

        self.root.after(0, self._refresh_ui)
        self.root.after(0, lambda: self.start_button.config(state="disabled"))

    def start_game(self) -> None:
        with self.lock:
            if not self.client_connected or not self.client_socket:
                messagebox.showwarning("Client belum terhubung", "Jalankan client terlebih dahulu.")
                return

            if self.game_preparing or self.game_active:
                return

            self.game_preparing = True
            self.game_active = False
            self.waiting_next_target = False
            self.score = 0
            self.time_left = GAME_DURATION_SECONDS
            self.active_emoji = self.emoji_manager.get_random_emoji()
            self.status = "Preparing Camera"
            self.round_id = 1

            round_id = self.round_id
            active_emoji = self.active_emoji

        self._safe_send("PREPARE_GAME", round_id, active_emoji, self.score, self.time_left)
        self._refresh_ui()

    def _handle_camera_ready(self) -> None:
        with self.lock:
            if not self.client_connected or not self.game_preparing:
                return

            self.game_preparing = False
            self.game_active = True
            self.status = "Game Started"
            round_id = self.round_id
            active_emoji = self.active_emoji
            score = self.score
            time_left = self.time_left

        self._safe_send("START_GAME", round_id, active_emoji, score, time_left)
        self.root.after(0, self._refresh_ui)

        timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        timer_thread.start()

    def _handle_camera_error(self) -> None:
        with self.lock:
            if not self.game_preparing:
                return

            self.game_preparing = False
            self.game_active = False
            self.waiting_next_target = False
            self.active_emoji = "-"
            self.status = "Camera Not Ready"

        self.root.after(0, self._refresh_ui)
        self.root.after(0, lambda: self.start_button.config(state="normal"))

    def _run_timer(self) -> None:
        while True:
            time.sleep(1)

            with self.lock:
                if not self.game_active:
                    return

                self.time_left -= 1
                time_left = self.time_left
                score = self.score
                active_emoji = self.active_emoji
                round_id = self.round_id

                if self.time_left <= 0:
                    self.game_active = False
                    self.status = "Game Over"

            if time_left <= 0:
                self._safe_send("END_GAME", score)
                self.root.after(0, self._refresh_ui)
                self.root.after(0, lambda: messagebox.showinfo("Game Over", f"Skor Akhir: {score}"))
                return

            self._safe_send("TICK", round_id, active_emoji, score, time_left)
            self.root.after(0, self._refresh_ui)

    def _handle_match(self, round_id_text: str) -> None:
        with self.lock:
            if (
                not self.game_active
                or self.waiting_next_target
                or round_id_text != str(self.round_id)
            ):
                return

            self.score += 1
            self.status = "MATCH - Next target soon"
            self.waiting_next_target = True
            score = self.score
            time_left = self.time_left

        self._safe_send("MATCHED", score, time_left)
        self.root.after(0, self._refresh_ui)

        delay = NEXT_TARGET_DELAY_SECONDS
        timer = threading.Timer(delay, self._send_next_target_after_match)
        timer.daemon = True
        timer.start()

    def _send_next_target_after_match(self) -> None:
        with self.lock:
            if not self.game_active or not self.waiting_next_target:
                return

            self.round_id += 1
            self.active_emoji = self.emoji_manager.get_random_emoji(self.active_emoji)
            self.waiting_next_target = False
            self.status = "New Target"

            round_id = self.round_id
            active_emoji = self.active_emoji
            score = self.score
            time_left = self.time_left

        self._safe_send("TARGET", round_id, active_emoji, score, time_left)
        self.root.after(0, self._refresh_ui)

    def _handle_no_match(self, round_id_text: str) -> None:
        with self.lock:
            if (
                not self.game_active
                or self.waiting_next_target
                or round_id_text != str(self.round_id)
            ):
                return
            self.status = "NO_MATCH"

        self.root.after(0, self._refresh_ui)

    def _safe_send(self, command: str, *parts: object) -> None:
        with self.lock:
            client_socket = self.client_socket

        if not client_socket:
            return

        try:
            with self.send_lock:
                send_message(client_socket, command, *parts)
        except OSError:
            with self.lock:
                self.client_connected = False
                self.game_active = False
                self.status = "Disconnected"
            self.root.after(0, self._refresh_ui)

    def _refresh_ui(self) -> None:
        with self.lock:
            self.client_status_var.set("Connected" if self.client_connected else "Disconnected")
            self.time_var.set(str(max(self.time_left, 0)))
            self.emoji_var.set(self.active_emoji)
            self.score_var.set(str(self.score))
            self.status_var.set(self.status)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = FaceFilterGameServer()
    app.run()
