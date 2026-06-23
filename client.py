"""TCP game client with webcam, FaceMesh detection, Tkinter UI, and music."""

from __future__ import annotations

import os
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk

import cv2
import pygame

from emoji_manager import get_expression_for_emoji
from expression_detector import ExpressionDetector
from protocol import HOST, PORT, decode_message, send_message


MUSIC_PATH = os.path.join("assets", "game_music.mp3")
CORRECT_SOUND_PATH = os.path.join("assets", "correct_music.mp3")
CORRECT_SOUND_VOLUME = 0.3


class FaceFilterGameClient:
    """Connect to the game server and run webcam-based expression detection."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Face Filter Game Client")
        self.root.geometry("760x620")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.socket: socket.socket | None = None
        self.socket_file = None
        self.send_lock = threading.Lock()

        self.detector = ExpressionDetector()
        self.camera: cv2.VideoCapture | None = None

        self.connected = False
        self.music_ready = False
        self.correct_sound: pygame.mixer.Sound | None = None
        self.camera_ready = False
        self.game_active = False
        self.round_id = ""
        self.target_emoji = "-"
        self.target_expression = "neutral"
        self.score = 0
        self.time_left = 0
        self.detected_expression = "-"
        self.sent_match_for_round = False
        self.last_no_match_sent_at = 0.0

        self.status_var = tk.StringVar(value="Connecting to server...")
        self.target_var = tk.StringVar(value="-")
        self.timer_var = tk.StringVar(value="0")
        self.score_var = tk.StringVar(value="0")
        self.detected_var = tk.StringVar(value="-")

        self._build_ui()
        self._setup_music()
        self._connect_to_server()

    def _build_ui(self) -> None:
        title = ttk.Label(
            self.root,
            text="Face Expression Guess Game",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(18, 10))

        info = ttk.Frame(self.root, padding=(18, 8))
        info.pack(fill="x")

        self._add_info_cell(info, "Target", self.target_var, 0)
        self._add_info_cell(info, "Timer", self.timer_var, 1)
        self._add_info_cell(info, "Skor", self.score_var, 2)
        self._add_info_cell(info, "Deteksi", self.detected_var, 3)

        self.video_label = ttk.Label(self.root)
        self.video_label.pack(pady=12)

        status = ttk.Label(self.root, textvariable=self.status_var, font=("Segoe UI", 11))
        status.pack(pady=(0, 12))

    @staticmethod
    def _add_info_cell(parent: ttk.Frame, label: str, variable: tk.StringVar, column: int) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky="nsew", padx=8)
        parent.columnconfigure(column, weight=1)

        ttk.Label(frame, text=label, font=("Segoe UI", 10)).pack()
        ttk.Label(frame, textvariable=variable, font=("Segoe UI", 20, "bold")).pack()

    def _setup_music(self) -> None:
        """Prepare background music if assets/game_music.mp3 exists."""
        try:
            pygame.mixer.init()
        except pygame.error as error:
            print(f"Audio tidak tersedia. Game berjalan tanpa musik: {error}")
            return

        if os.path.exists(MUSIC_PATH):
            try:
                pygame.mixer.music.load(MUSIC_PATH)
                self.music_ready = True
            except pygame.error as error:
                print(f"Gagal memuat musik. Game berjalan tanpa musik: {error}")
        else:
            print(f"{MUSIC_PATH} tidak ditemukan. Game tetap berjalan tanpa musik.")

        if os.path.exists(CORRECT_SOUND_PATH):
            try:
                self.correct_sound = pygame.mixer.Sound(CORRECT_SOUND_PATH)
                self.correct_sound.set_volume(CORRECT_SOUND_VOLUME)
            except pygame.error as error:
                print(f"Gagal memuat sound effect benar: {error}")
        else:
            print(f"{CORRECT_SOUND_PATH} tidak ditemukan. Sound effect benar tidak diputar.")

    def _connect_to_server(self) -> None:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST, PORT))
            self.socket_file = self.socket.makefile("r", encoding="utf-8")
            self.connected = True
            self.status_var.set("Connected. Menunggu server menekan START GAME.")

            thread = threading.Thread(target=self._listen_to_server, daemon=True)
            thread.start()
        except OSError as error:
            self.status_var.set(f"Gagal terhubung ke server: {error}")

    def _listen_to_server(self) -> None:
        while self.connected and self.socket_file:
            line = self.socket_file.readline()
            if not line:
                break

            message = decode_message(line)
            self.root.after(0, lambda msg=message: self._handle_server_message(msg))

        self.connected = False
        self.root.after(0, lambda: self.status_var.set("Koneksi server terputus."))

    def _handle_server_message(self, message) -> None:
        if message.command == "PREPARE_GAME" and len(message.parts) >= 4:
            self._prepare_game(message.parts)
        elif message.command == "START_GAME" and len(message.parts) >= 4:
            self._start_game(message.parts)
        elif message.command == "TARGET" and len(message.parts) >= 4:
            self._set_target(message.parts)
        elif message.command == "MATCHED" and len(message.parts) >= 2:
            self._handle_matched(message.parts)
        elif message.command == "TICK" and len(message.parts) >= 4:
            self._update_tick(message.parts)
        elif message.command == "END_GAME" and message.parts:
            self._end_game(message.parts[0])

    def _prepare_game(self, parts: list[str]) -> None:
        self.game_active = False
        self.camera_ready = False
        self._set_target(parts)
        self.status_var.set("Menyiapkan kamera...")

        if self._open_camera():
            self._wait_until_camera_ready()
        else:
            self._safe_send("CAMERA_ERROR")

    def _start_game(self, parts: list[str]) -> None:
        self.game_active = True
        self._set_target(parts)
        self.status_var.set("Game berjalan. Ikuti emoji target dari server.")
        self._play_music()
        self._update_camera_frame()

    def _set_target(self, parts: list[str]) -> None:
        self.round_id = parts[0]
        self.target_emoji = parts[1]
        self.score = int(parts[2])
        self.time_left = int(parts[3])
        self.target_expression = get_expression_for_emoji(self.target_emoji)
        self.sent_match_for_round = False
        self.last_no_match_sent_at = 0.0

        self.target_var.set(self.target_emoji)
        self.score_var.set(str(self.score))
        self.timer_var.set(str(self.time_left))

    def _handle_matched(self, parts: list[str]) -> None:
        self.score = int(parts[0])
        self.time_left = int(parts[1])
        self.score_var.set(str(self.score))
        self.timer_var.set(str(self.time_left))
        self.status_var.set("Cocok. Bersiap untuk target berikutnya...")
        self._play_correct_sound()

    def _update_tick(self, parts: list[str]) -> None:
        self.round_id = parts[0]
        self.target_emoji = parts[1]
        self.score = int(parts[2])
        self.time_left = int(parts[3])
        self.target_expression = get_expression_for_emoji(self.target_emoji)

        self.target_var.set(self.target_emoji)
        self.score_var.set(str(self.score))
        self.timer_var.set(str(self.time_left))

    def _open_camera(self) -> bool:
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            self.status_var.set("Webcam tidak bisa dibuka.")
            self.game_active = False
            return False

        return True

    def _wait_until_camera_ready(self, attempts_left: int = 20) -> None:
        if self.camera is None:
            self._safe_send("CAMERA_ERROR")
            return

        success, frame = self.camera.read()
        if success:
            self.camera_ready = True
            frame = cv2.flip(frame, 1)
            self._draw_overlay(frame, "ready")
            self._show_frame(frame)
            self.status_var.set("Kamera siap. Menunggu server memulai countdown...")
            self._safe_send("CAMERA_READY")
            return

        if attempts_left <= 0:
            self.status_var.set("Kamera belum siap. Coba jalankan ulang client.")
            self._safe_send("CAMERA_ERROR")
            self._release_camera()
            return

        self.root.after(100, lambda: self._wait_until_camera_ready(attempts_left - 1))

    def _update_camera_frame(self) -> None:
        if not self.game_active or self.camera is None:
            return

        success, frame = self.camera.read()
        if not success:
            self.status_var.set("Gagal membaca frame dari webcam.")
            self.root.after(100, self._update_camera_frame)
            return

        frame = cv2.flip(frame, 1)
        expression_result = self.detector.detect(frame)
        self.detected_expression = expression_result.expression
        self.detected_var.set(self.detected_expression)

        self._send_detection_result(expression_result.expression)
        self._draw_overlay(frame, expression_result.expression)
        self._show_frame(frame)

        self.root.after(30, self._update_camera_frame)

    def _send_detection_result(self, expression: str) -> None:
        if not self.socket or not self.round_id:
            return

        is_match = expression == self.target_expression

        if is_match and not self.sent_match_for_round:
            self._safe_send("MATCH", self.round_id)
            self.sent_match_for_round = True
            return

        # NO_MATCH is throttled so the server is not flooded with webcam frames.
        now = time.time()
        if not is_match and now - self.last_no_match_sent_at > 0.35:
            self._safe_send("NO_MATCH", self.round_id)
            self.last_no_match_sent_at = now

    def _draw_overlay(self, frame, expression: str) -> None:
        text = f"Target: {self.target_emoji} | Deteksi: {expression}"
        cv2.putText(
            frame,
            text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    def _show_frame(self, frame) -> None:
        frame = cv2.resize(frame, (700, 420))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Tkinter can display PPM bytes directly, so no Pillow dependency is
        # needed for this beginner-friendly project.
        height, width, _ = rgb_frame.shape
        ppm_header = f"P6\n{width} {height}\n255\n".encode("ascii")
        image = tk.PhotoImage(data=ppm_header + rgb_frame.tobytes(), format="PPM")

        self.video_label.configure(image=image, text="")
        self.video_label.image = image

    def _play_music(self) -> None:
        if not self.music_ready:
            return

        if pygame.mixer.music.get_busy():
            return

        try:
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def _play_correct_sound(self) -> None:
        if self.correct_sound is None:
            return

        try:
            self.correct_sound.play()
        except pygame.error:
            pass

    def _safe_send(self, command: str, *parts: object) -> None:
        if not self.socket:
            return

        try:
            with self.send_lock:
                send_message(self.socket, command, *parts)
        except OSError:
            self.connected = False
            self.status_var.set("Gagal mengirim pesan ke server.")

    def _end_game(self, final_score: str) -> None:
        self.game_active = False
        self.score_var.set(final_score)
        self.status_var.set(f"GAME OVER - Skor Akhir: {final_score}")
        self.target_var.set("-")
        self.detected_var.set("-")
        if self.music_ready:
            pygame.mixer.music.stop()
        self._release_camera()
        self._show_game_over_screen(final_score)

    def _show_game_over_screen(self, final_score: str) -> None:
        self.video_label.configure(
            image="",
            text=f"GAME OVER\n\nSkor Akhir: {final_score}",
            font=("Segoe UI", 24, "bold"),
        )
        self.video_label.image = None

    def _release_camera(self) -> None:
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def close(self) -> None:
        self.game_active = False
        self.connected = False
        if self.music_ready:
            pygame.mixer.music.stop()
        self._release_camera()
        self.detector.close()

        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass

        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = FaceFilterGameClient()
    app.run()
