"""
main.py
-------
AI Virtual Hand Control Mouse
==============================
Entry point — ties together the webcam loop, hand tracker,
gesture engine, cursor controller, and HUD.

Usage:
    python main.py [--cam 0] [--width 640] [--height 480]
                   [--smooth 0.18] [--pinch 38] [--cooldown 0.6]

Hotkeys (focus the camera window):
    Q         – quit
    Space     – toggle mouse control on/off
    H         – toggle HUD overlay
"""

import argparse
import sys
import cv2

from hand_tracker      import HandTracker
from gesture_engine    import GestureEngine, Gesture
from cursor_controller import CursorController
from hud               import HUD


def parse_args():
    p = argparse.ArgumentParser(description="AI Virtual Hand Mouse")
    p.add_argument("--cam",      type=int,   default=0,    help="Camera index (default 0)")
    p.add_argument("--width",    type=int,   default=640,  help="Capture width")
    p.add_argument("--height",   type=int,   default=480,  help="Capture height")
    p.add_argument("--smooth",   type=float, default=0.18, help="Cursor EMA smoothing 0-1")
    p.add_argument("--pinch",    type=int,   default=38,   help="Pinch click threshold px")
    p.add_argument("--cooldown", type=float, default=0.6,  help="Click cooldown seconds")
    return p.parse_args()


def open_camera(index: int, w: int, h: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera index {index}.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def main():
    args = parse_args()

    print("=" * 52)
    print("  AI Virtual Hand Control Mouse")
    print("=" * 52)
    print(f"  Camera : {args.cam}  |  Resolution: {args.width}x{args.height}")
    print(f"  Smooth : {args.smooth}  |  Pinch px : {args.pinch}")
    print("  Press Q in the camera window to quit.")
    print("=" * 52)

    cap        = open_camera(args.cam, args.width, args.height)
    tracker    = HandTracker()
    gestures = GestureEngine()
    cursor     = CursorController(
        cam_w=args.width,
        cam_h=args.height,
        smooth=args.smooth,
        click_cooldown=args.cooldown,
    )
    hud        = HUD(cam_w=args.width, cam_h=args.height)
    ctrl_enabled = True

    cv2.namedWindow("Hand Mouse", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hand Mouse", args.width, args.height)

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[WARN] Dropped frame — retrying...")
            continue

        # Mirror so movements feel natural
        frame = cv2.flip(frame, 1)

        # Hand detection + landmark overlay
        frame = tracker.process_frame(frame)

        # Gesture classification
        gesture = gestures.classify(tracker)

        # Scroll delta (only relevant during SCROLL gesture)
        scroll_delta = 0
        if gesture == Gesture.SCROLL:
            scroll_delta = gestures.scroll_delta(tracker)

        # Move the real mouse cursor
        if ctrl_enabled:
            cursor.update(tracker, gesture, scroll_delta)

        # HUD
        pinch_d = tracker.pinch_distance()
        frame = hud.draw(frame, gesture, enabled=ctrl_enabled, pinch_dist=pinch_d)

        cv2.imshow("Hand Mouse", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            ctrl_enabled = not ctrl_enabled
            state = "ENABLED" if ctrl_enabled else "DISABLED"
            print(f"  [*] Mouse control {state}")
        elif key == ord('h'):
            hud.toggle()

    # Cleanup
    tracker.release()
    cap.release()
    cv2.destroyAllWindows()
    print("  Bye!")


if __name__ == "__main__":
    main()
