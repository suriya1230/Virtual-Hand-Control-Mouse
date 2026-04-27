"""
gesture_engine.py  —  Final gesture map
-----------------------------------------
  1 finger  (index only)          →  MOVE
  2 fingers (index + middle)      →  LEFT_CLICK
  3 fingers (index+middle+ring)   →  RIGHT_CLICK
  Closed fist + move up/down      →  SCROLL
  Pinch (thumb + index touch)     →  DRAG
  Thumb up (others folded)        →  DOUBLE_CLICK
  Open palm / no hand             →  NONE
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import time
from hand_tracker import HandTracker, WRIST, THUMB_TIP, INDEX_TIP


class Gesture(Enum):
    NONE         = auto()
    MOVE         = auto()
    LEFT_CLICK   = auto()
    RIGHT_CLICK  = auto()
    SCROLL       = auto()
    DRAG         = auto()
    DOUBLE_CLICK = auto()


# Frames each gesture must be held before confirming
DWELL = {
    Gesture.NONE:         1,
    Gesture.MOVE:         1,
    Gesture.LEFT_CLICK:   8,
    Gesture.RIGHT_CLICK:  8,
    Gesture.SCROLL:       2,
    Gesture.DRAG:         10,
    Gesture.DOUBLE_CLICK: 8,
}

PINCH_THRESHOLD       = 40   # px — thumb-index distance for pinch/drag
SCROLL_MOVE_THRESHOLD = 3    # px wrist delta per frame to confirm scroll


@dataclass
class State:
    candidate:    object = None
    dwell:        int    = 0
    current:      object = None
    prev_wrist_y: int    = 0

    def __post_init__(self):
        self.candidate = Gesture.NONE
        self.current   = Gesture.NONE


class GestureEngine:
    def __init__(self, pinch_threshold: int = PINCH_THRESHOLD):
        self.pinch_threshold = pinch_threshold
        self.state = State()

    def classify(self, tracker: HandTracker) -> Gesture:
        if not tracker.hand_detected():
            self._reset()
            return Gesture.NONE

        fingers = tracker.fingers_up()        # [thumb, idx, mid, ring, pinky]
        thumb, idx, mid, ring, pinky = fingers
        pinch   = tracker.pinch_distance()
        s       = self.state

        # ── PINCH → DRAG (takes priority, checked first) ─────────────
        if pinch < self.pinch_threshold and not (thumb and not idx and not mid):
            # exclude thumb-up pose from being mistaken for pinch
            raw = Gesture.DRAG

        # ── THUMB UP only → DOUBLE CLICK ─────────────────────────────
        elif thumb and not idx and not mid and not ring and not pinky:
            raw = Gesture.DOUBLE_CLICK

        # ── 1 finger (index only) → MOVE ─────────────────────────────
        elif idx and not mid and not ring and not pinky and not thumb:
            raw = Gesture.MOVE

        # ── 2 fingers (index + middle) → LEFT CLICK ──────────────────
        elif idx and mid and not ring and not pinky:
            raw = Gesture.LEFT_CLICK

        # ── 3 fingers (index+middle+ring) → RIGHT CLICK ──────────────
        elif idx and mid and ring and not pinky:
            raw = Gesture.RIGHT_CLICK

        # ── Closed fist (0 non-thumb fingers) + wrist move → SCROLL ──
        elif not idx and not mid and not ring and not pinky:
            wrist_y = tracker.lm_list[WRIST][1]
            delta   = abs(wrist_y - s.prev_wrist_y)
            s.prev_wrist_y = wrist_y
            raw = Gesture.SCROLL if delta >= SCROLL_MOVE_THRESHOLD else Gesture.NONE

        else:
            raw = Gesture.NONE

        return self._dwell(raw)

    def scroll_delta(self, tracker: HandTracker) -> int:
        """Positive = hand moving down = scroll down."""
        if not tracker.hand_detected():
            return 0
        wrist_y = tracker.lm_list[WRIST][1]
        delta = wrist_y - self.state.prev_wrist_y
        self.state.prev_wrist_y = wrist_y
        return delta

    def _dwell(self, raw: Gesture) -> Gesture:
        s = self.state
        if raw == s.candidate:
            s.dwell += 1
        else:
            s.candidate = raw
            s.dwell     = 0
        if s.dwell >= DWELL.get(raw, 1):
            s.current = raw
        return s.current

    def _reset(self):
        self.state = State()