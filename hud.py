"""
hud.py — On-screen overlay with updated gesture labels
"""

import time
import cv2
import numpy as np
from gesture_engine import Gesture

GESTURE_STYLE = {
    Gesture.NONE:         ("No action",     (120, 120, 120)),
    Gesture.MOVE:         ("Moving",        (255, 200,  50)),
    Gesture.LEFT_CLICK:   ("Left Click",    ( 50, 220,  50)),
    Gesture.RIGHT_CLICK:  ("Right Click",   ( 50, 100, 255)),
    Gesture.SCROLL:       ("Scroll",        (200,  50, 255)),
    Gesture.DRAG:         ("Drag",          (255, 140,   0)),
    Gesture.DOUBLE_CLICK: ("Double Click",  ( 20, 200, 180)),
}

GESTURE_ICON = {
    Gesture.NONE:         " ",
    Gesture.MOVE:         "->",
    Gesture.LEFT_CLICK:   "L",
    Gesture.RIGHT_CLICK:  "R",
    Gesture.SCROLL:       "~",
    Gesture.DRAG:         "D",
    Gesture.DOUBLE_CLICK: "LL",
}


class HUD:
    def __init__(self, cam_w=640, cam_h=480):
        self.cam_w  = cam_w
        self.cam_h  = cam_h
        self._fps_t = time.monotonic()
        self._fps   = 0.0
        self._active = True

    def toggle(self):
        self._active = not self._active

    def draw(self, frame, gesture, enabled=True, pinch_dist=0):
        now = time.monotonic()
        self._fps = 0.9 * self._fps + 0.1 * (1 / max(now - self._fps_t, 1e-6))
        self._fps_t = now

        if not self._active:
            return frame

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.cam_w, 54), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        label, color = GESTURE_STYLE.get(gesture, ("?", (255,255,255)))
        icon         = GESTURE_ICON.get(gesture, "?")

        cv2.rectangle(frame, (10, 8), (150, 44), color, -1)
        cv2.rectangle(frame, (10, 8), (150, 44), (255,255,255), 1)
        cv2.putText(frame, f"{icon}  {label}", (18, 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0,0,0), 2, cv2.LINE_AA)

        cv2.putText(frame, f"FPS: {self._fps:.0f}",
                    (self.cam_w - 115, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (200,200,200), 1, cv2.LINE_AA)

        status_color = (50, 220, 50) if enabled else (50, 50, 220)
        cv2.putText(frame, "ON" if enabled else "OFF",
                    (self.cam_w - 220, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 1, cv2.LINE_AA)

        legend = ["Q: Quit", "Space: Toggle", "H: HUD"]
        for i, line in enumerate(legend):
            cv2.putText(frame, line,
                        (self.cam_w - 130, self.cam_h - 10 - i * 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (150,150,150), 1, cv2.LINE_AA)
        return frame