"""
hand_tracker.py  —  Debug + Robust version
- Prints detected fingers every 30 frames so you can see what's detected
- Uses both Y-position AND distance methods combined
- More lenient thresholds
"""

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import HandLandmarkerOptions
from mediapipe import Image, ImageFormat
import urllib.request
import os
import time

WRIST      = 0
THUMB_CMC  = 1
THUMB_MCP  = 2
THUMB_IP   = 3
THUMB_TIP  = 4
INDEX_MCP  = 5
INDEX_PIP  = 6
INDEX_DIP  = 7
INDEX_TIP  = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12
RING_MCP   = 13
RING_PIP   = 14
RING_DIP   = 15
RING_TIP   = 16
PINKY_MCP  = 17
PINKY_PIP  = 18
PINKY_DIP  = 19
PINKY_TIP  = 20

MODEL_PATH = "hand_landmarker.task"
MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17),
]

def _download_model():
    if not os.path.exists(MODEL_PATH):
        print("  [*] Downloading MediaPipe hand model (~3 MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("  [*] Done.")

def _dist(p1, p2):
    return np.hypot(p1[0]-p2[0], p1[1]-p2[1])


class HandTracker:
    def __init__(self, max_hands=1, detection_confidence=0.60, tracking_confidence=0.60):
        _download_model()
        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
            min_hand_presence_confidence=detection_confidence,
        )
        self._detector  = mp_vision.HandLandmarker.create_from_options(options)
        self._start_ms  = int(time.time() * 1000)
        self._frame_n   = 0
        self.landmarks  = None
        self.lm_list    = []

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        self.lm_list   = []
        self.landmarks = None
        self._frame_n += 1

        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
        ts_ms    = int(time.time() * 1000) - self._start_ms
        result   = self._detector.detect_for_video(mp_image, ts_ms)

        if result.hand_landmarks:
            lms = result.hand_landmarks[0]
            self.landmarks = lms
            self.lm_list   = [(int(lm.x * w), int(lm.y * h)) for lm in lms]
            self._draw_landmarks(frame)

            # ── Debug: print fingers every 30 frames ──
            if self._frame_n % 30 == 0:
                fu = self.fingers_up()
                names = ['Thumb','Index','Middle','Ring','Pinky']
                up = [names[i] for i,v in enumerate(fu) if v]
                print(f"  [DEBUG] Fingers UP: {up if up else 'none'} | pinch={self.pinch_distance():.0f}px")

        return frame

    def hand_detected(self) -> bool:
        return len(self.lm_list) == 21

    def get_point(self, idx):
        return self.lm_list[idx] if self.hand_detected() else None

    # ------------------------------------------------------------------
    # Finger extension — triple method for robustness
    # ------------------------------------------------------------------

    def _finger_extended(self, tip, dip, pip, mcp) -> bool:
        """
        Extended = ANY TWO of three checks pass:
          1. Tip Y above PIP Y (classic upright check)
          2. dist(wrist→tip) > dist(wrist→mcp) * 1.3
          3. dist(tip→mcp)   > dist(pip→mcp)   * 1.15
        This is much more robust than any single check.
        """
        if not self.hand_detected():
            return False

        lm      = self.lm_list
        wrist   = lm[WRIST]

        # Check 1: tip higher than PIP (Y axis, works for upright hand)
        c1 = lm[tip][1] < lm[pip][1]

        # Check 2: tip far from wrist compared to knuckle
        c2 = _dist(wrist, lm[tip]) > _dist(wrist, lm[mcp]) * 1.3

        # Check 3: tip-to-knuckle distance > pip-to-knuckle distance
        c3 = _dist(lm[tip], lm[mcp]) > _dist(lm[pip], lm[mcp]) * 1.15

        return sum([c1, c2, c3]) >= 2   # pass if 2+ checks agree

    def thumb_extended(self) -> bool:
        if not self.hand_detected():
            return False
        lm    = self.lm_list
        wrist = lm[WRIST]
        c1 = _dist(wrist, lm[THUMB_TIP]) > _dist(wrist, lm[THUMB_IP]) * 1.2
        c2 = _dist(lm[THUMB_TIP], lm[THUMB_MCP]) > _dist(lm[THUMB_IP], lm[THUMB_MCP]) * 1.1
        # Also check horizontal spread from index MCP
        c3 = _dist(lm[THUMB_TIP], lm[INDEX_MCP]) > _dist(lm[THUMB_CMC], lm[INDEX_MCP]) * 0.8
        return sum([c1, c2, c3]) >= 2

    def fingers_up(self) -> list:
        if not self.hand_detected():
            return [False] * 5
        return [
            self.thumb_extended(),
            self._finger_extended(INDEX_TIP,  INDEX_DIP,  INDEX_PIP,  INDEX_MCP),
            self._finger_extended(MIDDLE_TIP, MIDDLE_DIP, MIDDLE_PIP, MIDDLE_MCP),
            self._finger_extended(RING_TIP,   RING_DIP,   RING_PIP,   RING_MCP),
            self._finger_extended(PINKY_TIP,  PINKY_DIP,  PINKY_PIP,  PINKY_MCP),
        ]

    def pinch_distance(self) -> float:
        if not self.hand_detected():
            return float('inf')
        return _dist(self.lm_list[THUMB_TIP], self.lm_list[INDEX_TIP])

    def _draw_landmarks(self, frame):
        pts  = self.lm_list
        tips = {THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP}

        # Draw connections
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 200, 100), 2, cv2.LINE_AA)

        # Draw joints — green for tips, white for rest
        for i, (x, y) in enumerate(pts):
            color = (0, 255, 80) if i in tips else (255, 255, 255)
            r = 7 if i in tips else 4
            cv2.circle(frame, (x, y), r, color,       -1, cv2.LINE_AA)
            cv2.circle(frame, (x, y), r, (0, 130, 60), 1, cv2.LINE_AA)

        # Draw finger state on frame
        fu    = self.fingers_up()
        names = ['T','I','M','R','P']
        x0    = 10
        for i, (name, state) in enumerate(zip(names, fu)):
            col = (0, 220, 80) if state else (80, 80, 80)
            cv2.putText(frame, name, (x0 + i*22, frame.shape[0]-35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2, cv2.LINE_AA)

    def release(self):
        self._detector.close()