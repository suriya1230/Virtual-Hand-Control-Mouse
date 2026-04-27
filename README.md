# AI Virtual Hand Control Mouse

Control your computer mouse using only your hand and webcam — no hardware required.

## How it works

```
Webcam → MediaPipe (21 landmarks) → Gesture Classifier → Cursor Controller → OS Mouse
```

---

## Gesture Reference

| Hand Sign | Fingers | Action |
|---|---|---|
| ☝️ | Index finger only up | **Move cursor** |
| ✌️ | Index + Middle up | **Left click** |
| 🤟 | Index + Middle + Ring up | **Right click** |
| ✊ + move up/down | Closed fist, move hand vertically | **Scroll** |
| 🤏 | Thumb + Index touch (pinch) | **Drag** |
| 👍 | Thumb up only | **Double click** |
| 🖐️ | Open palm / no hand | **No action (pause)** |

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A working webcam
- Good lighting (lamp in front of you, not behind)
- On Linux: `sudo apt install python3-tk python3-dev scrot`
- On macOS: grant Terminal/Python **Accessibility** + **Screen Recording** permissions in
  *System Settings → Privacy & Security*

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> On first run, the app auto-downloads the MediaPipe hand model (~3 MB).

### 3. Run

```bash
python main.py
```

---

## Command Line Options

| Option | Default | Description |
|---|---|---|
| `--cam` | `0` | Camera index (try `1` or `2` if webcam not detected) |
| `--width` | `640` | Capture frame width |
| `--height` | `480` | Capture frame height |
| `--smooth` | `0.18` | Cursor smoothing (0.0 = very smooth, 1.0 = raw/fast) |
| `--pinch` | `40` | Pinch distance threshold in pixels for drag |
| `--cooldown` | `0.6` | Seconds between allowed clicks |

Example:
```bash
python main.py --cam 1 --smooth 0.22 --pinch 45
```

---

## Hotkeys

Focus the camera window first, then press:

| Key | Action |
|---|---|
| `Q` | Quit |
| `Space` | Toggle mouse control on / off |
| `H` | Toggle HUD overlay |

---

## File Structure

```
hand_mouse/
├── main.py              # Entry point — main webcam loop
├── hand_tracker.py      # MediaPipe wrapper, 21-landmark extraction
├── gesture_engine.py    # Gesture classification with dwell filter
├── cursor_controller.py # EMA smoothing + PyAutoGUI mouse events
├── hud.py               # On-screen overlay (gesture label, FPS, finger state)
└── requirements.txt     # Python dependencies
```

---

## Tuning Tips

| Problem | Fix |
|---|---|
| Cursor too jittery | Lower `--smooth` (e.g. `0.10`) |
| Cursor too slow / sluggish | Raise `--smooth` (e.g. `0.30`) |
| Gestures not detected | Improve lighting — lamp facing your hand |
| Wrong camera opens | Try `--cam 1` or `--cam 2` |
| Drag triggers too easily | Raise `--pinch` (e.g. `50`) |
| Drag not triggering | Lower `--pinch` (e.g. `28`) |
| Index finger not detected | Keep hand upright, fingers clearly spread |

---

## Lighting Tips

MediaPipe hand detection works best when:
- Your hand is well lit from the **front** (not backlit by a bright window)
- Background is plain and not too busy
- Hand is **30–50 cm** from the webcam
- Fingers are clearly visible and not overlapping

---

## Platform Notes

**Windows** — works out of the box.

**macOS** — PyAutoGUI requires Accessibility permission:
*System Settings → Privacy & Security → Accessibility → add Terminal or Python*

**Linux (X11)** — install `python3-tk` and `scrot`.
Wayland users: set `QT_QPA_PLATFORM=xcb` if the window does not open.

---

## Requirements

```
opencv-python>=4.9.0
mediapipe>=0.10.9
pyautogui>=0.9.54
numpy>=1.26.0
```
