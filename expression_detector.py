"""Simple expression detector based on MediaPipe FaceMesh landmarks.

This module does not use an external AI model. MediaPipe finds face landmarks,
then we calculate basic mouth ratios:

- surprise: mouth opening is large
- smile: mouth width is wide
- neutral: default expression when neither condition is strong enough

Thresholds are intentionally easy to tune for class projects because webcams,
lighting, and face distance can change the measured ratios.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

import cv2

import mediapipe as mp

try:
    mp_face_mesh = mp.solutions.face_mesh
except AttributeError as error:
    raise RuntimeError(
        "MediaPipe FaceMesh legacy API tidak ditemukan. "
        "Project ini membutuhkan mediapipe==0.10.14. "
        "Install dependency dengan: python -m pip install -r requirements.txt"
    ) from error


@dataclass(frozen=True)
class ExpressionResult:
    expression: str
    mouth_width_ratio: float
    mouth_open_ratio: float
    face_detected: bool


class ExpressionDetector:
    """Detect smile, surprise, or neutral from webcam frames."""

    def __init__(self) -> None:
        self._face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def detect(self, frame) -> ExpressionResult:
        """Return the current facial expression for one OpenCV BGR frame."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._face_mesh.process(rgb_frame)

        if not result.multi_face_landmarks:
            return ExpressionResult(
                expression="unknown",
                mouth_width_ratio=0.0,
                mouth_open_ratio=0.0,
                face_detected=False,
            )

        landmarks = result.multi_face_landmarks[0].landmark

        # Face width gives a stable reference so mouth size still works when
        # the user moves closer to or farther from the camera.
        face_width = self._distance(landmarks[234], landmarks[454])
        mouth_width = self._distance(landmarks[61], landmarks[291])
        mouth_open = self._distance(landmarks[13], landmarks[14])

        if face_width == 0:
            face_width = 1.0

        mouth_width_ratio = mouth_width / face_width
        mouth_open_ratio = mouth_open / face_width

        if mouth_open_ratio > 0.075:
            expression = "surprise"
        elif mouth_width_ratio > 0.42:
            expression = "smile"
        else:
            expression = "neutral"

        return ExpressionResult(
            expression=expression,
            mouth_width_ratio=mouth_width_ratio,
            mouth_open_ratio=mouth_open_ratio,
            face_detected=True,
        )

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._face_mesh.close()

    @staticmethod
    def _distance(point_a, point_b) -> float:
        return hypot(point_a.x - point_b.x, point_a.y - point_b.y)
