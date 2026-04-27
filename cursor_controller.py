"""
cursor_controller.py
--------------------
Maps hand landmarks to OS mouse events.
Handles: MOVE, LEFT_CLICK, RIGHT_CLICK, DOUBLE_CLICK, DRAG, SCROLL
"""

import time
import pyautogui
import numpy as np
from gesture_engine import Gesture
from hand_tracker import HandTracker, INDEX_TIP, THUMB_TIP, WRIST

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0


class CursorController:
    def __init__(
        self,
        cam_w: int        = 640,
        cam_h: int        = 480,
        screen_w: int     = None,
        screen_h: int     = None,
        smooth: float     = 0.18,
        click_cooldown: float = 0.6,
        scroll_speed: float   = 0.5,
    ):
        sw, sh = pyautogui.size()
        self.screen_w      = screen_w or sw
        self.screen_h      = screen_h or sh
        self.cam_w         = cam_w
        self.cam_h         = cam_h
        self.smooth        = smooth
        self.click_cooldown = click_cooldown
        self.scroll_speed  = scroll_speed

        self._sx: float = self.screen_w / 2
        self._sy: float = self.screen_h / 2
        self._last_click_time: float = 0
        self._dragging: bool         = False
        self._last_gesture: Gesture  = Gesture.NONE

    def update(self, tracker: HandTracker, gesture: Gesture, scroll_delta: int = 0):
        if gesture == Gesture.NONE:
            self._release_drag()
            self._last_gesture = gesture
            return

        # Use index tip for move/click; wrist for scroll/drag
        tip = tracker.get_point(INDEX_TIP)
        if tip is None:
            return

        margin = 0.10
        nx = np.clip((tip[0] / self.cam_w - margin) / (1 - 2 * margin), 0, 1)
        ny = np.clip((tip[1] / self.cam_h - margin) / (1 - 2 * margin), 0, 1)

        self._sx = self._sx * (1 - self.smooth) + nx * self.screen_w * self.smooth
        self._sy = self._sy * (1 - self.smooth) + ny * self.screen_h * self.smooth

        sx = int(self._sx)
        sy = int(self._sy)

        if gesture == Gesture.MOVE:
            self._release_drag()
            pyautogui.moveTo(sx, sy)

        elif gesture == Gesture.LEFT_CLICK:
            self._release_drag()
            pyautogui.moveTo(sx, sy)
            self._try_click(sx, sy, button='left')

        elif gesture == Gesture.RIGHT_CLICK:
            self._release_drag()
            pyautogui.moveTo(sx, sy)
            self._try_click(sx, sy, button='right')

        elif gesture == Gesture.DOUBLE_CLICK:
            self._release_drag()
            pyautogui.moveTo(sx, sy)
            self._try_double_click(sx, sy)

        elif gesture == Gesture.DRAG:
            if not self._dragging:
                pyautogui.mouseDown(sx, sy, button='left')
                self._dragging = True
            else:
                pyautogui.moveTo(sx, sy)

        elif gesture == Gesture.SCROLL:
            self._release_drag()
            clicks = int(scroll_delta * self.scroll_speed)
            if clicks != 0:
                pyautogui.scroll(-clicks)

        self._last_gesture = gesture

    def _try_click(self, x, y, button='left'):
        now = time.monotonic()
        if now - self._last_click_time >= self.click_cooldown:
            pyautogui.click(x, y, button=button)
            self._last_click_time = now

    def _try_double_click(self, x, y):
        now = time.monotonic()
        if now - self._last_click_time >= self.click_cooldown:
            pyautogui.doubleClick(x, y)
            self._last_click_time = now

    def _release_drag(self):
        if self._dragging:
            pyautogui.mouseUp(button='left')
            self._dragging = False