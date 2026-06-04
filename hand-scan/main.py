import cv2
import mediapipe as mp
import math
import time
import numpy as np

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

scan_start = None
scan_duration = 3
play_video = False
scan_complete_flash = 0  

video = cv2.VideoCapture("hand-scan/source/vidio.mp4")

C_BG_OVERLAY  = (10, 10, 20)
C_GREEN       = (0, 220, 100)
C_CYAN        = (255, 220, 0)
C_WHITE       = (240, 240, 240)
C_DIM         = (80, 80, 90)
C_RED         = (50, 50, 220)
C_YELLOW      = (0, 220, 220)
C_ACCENT      = (200, 255, 80)

def draw_corner_brackets(frame, x1, y1, x2, y2, color, thickness=2, length=20):
    pts = [
        ((x1, y1), (x1 + length, y1), (x1, y1 + length)),
        ((x2, y1), (x2 - length, y1), (x2, y1 + length)),
        ((x1, y2), (x1 + length, y2), (x1, y2 - length)),
        ((x2, y2), (x2 - length, y2), (x2, y2 - length)),
    ]
    for corner in pts:
        cv2.line(frame, corner[0], corner[1], color, thickness)
        cv2.line(frame, corner[0], corner[2], color, thickness)

def draw_overlay(frame, x1, y1, x2, y2, color, alpha=0.15):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_scanlines(frame, y1, y2, x1, x2, alpha=0.08):
    overlay = frame.copy()
    for y in range(y1, y2, 4):
        cv2.line(overlay, (x1, y), (x2, y), (0, 0, 0), 1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_animated_dots(frame, x1, y1, x2, y2, tick, color):
    corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
    r = 4 + int(2 * abs(math.sin(tick * 0.1)))
    for cx, cy in corners:
        cv2.circle(frame, (cx, cy), r, color, -1)

def draw_status_bar(frame, w, h, tick):
    cv2.rectangle(frame, (0, 0), (w, 38), (10, 10, 20), -1)
    cv2.line(frame, (0, 38), (w, 38), C_CYAN, 1)

    ts = time.strftime("%H:%M:%S")
    cv2.putText(frame, ts, (w - 110, 26),
                cv2.FONT_HERSHEY_DUPLEX, 0.6, C_DIM, 1, cv2.LINE_AA)

    dot_color = C_GREEN if (tick // 15) % 2 == 0 else C_DIM
    cv2.circle(frame, (w - 130, 18), 5, dot_color, -1)

def draw_bottom_bar(frame, w, h):
    cv2.rectangle(frame, (0, h - 36), (w, h), (10, 10, 20), -1)
    cv2.line(frame, (0, h - 36), (w, h - 36), C_CYAN, 1)
    tips = ""
    cv2.putText(frame, tips, (14, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_DIM, 1, cv2.LINE_AA)

def draw_scan_box(frame, x1, y1, x2, y2, state, elapsed, scan_duration, tick):
    """
    state: 'idle' | 'ready' | 'scanning' | 'complete'
    """
    color_map = {
        'idle':     C_DIM,
        'ready':    C_CYAN,
        'scanning': C_GREEN,
        'complete': C_ACCENT,
    }
    color = color_map.get(state, C_DIM)


    alpha_map = {'idle': 0.04, 'ready': 0.08, 'scanning': 0.12, 'complete': 0.25}
    draw_overlay(frame, x1, y1, x2, y2, color, alpha_map.get(state, 0.06))

    draw_scanlines(frame, y1, y2, x1, x2)

    blink = (tick // 10) % 2 == 0
    border_color = color if (state != 'idle' or blink) else C_DIM
    cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 1)

    draw_corner_brackets(frame, x1, y1, x2, y2, color, thickness=3, length=28)

    draw_animated_dots(frame, x1, y1, x2, y2, tick, color)

    label_map = {
        'idle':     "POSISIKAN TANGAN",
        'ready':    "TANGAN TERDETEKSI",
        'scanning': "SCANNING...",
        'complete': "SCAN SELESAI!",
    }
    label = label_map.get(state, "")
    lx = x1
    ly = y1 - 12
    cv2.putText(frame, label, (lx, ly),
                cv2.FONT_HERSHEY_DUPLEX, 0.55, color, 1, cv2.LINE_AA)

    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    ch_len = 10
    cv2.line(frame, (cx - ch_len, cy), (cx + ch_len, cy), color, 1)
    cv2.line(frame, (cx, cy - ch_len), (cx, cy + ch_len), color, 1)
    cv2.circle(frame, (cx, cy), 3, color, -1)

    if state == 'scanning':
        bar_x1, bar_y = x1, y2 + 14
        bar_w = x2 - x1
        bar_h = 10
        progress = min(elapsed / scan_duration, 1.0)
        filled = int(bar_w * progress)
        pct = int(progress * 100)

        cv2.rectangle(frame, (bar_x1, bar_y), (bar_x1 + bar_w, bar_y + bar_h), (30, 30, 40), -1)
        cv2.rectangle(frame, (bar_x1, bar_y), (bar_x1 + bar_w, bar_y + bar_h), C_DIM, 1)

        if filled > 0:
            cv2.rectangle(frame, (bar_x1, bar_y), (bar_x1 + filled, bar_y + bar_h), C_GREEN, -1)
            cv2.rectangle(frame, (bar_x1, bar_y), (bar_x1 + filled, bar_y + 2), C_ACCENT, -1)

        cv2.putText(frame, f"{pct}%", (bar_x1 + bar_w + 8, bar_y + bar_h - 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, C_GREEN, 1, cv2.LINE_AA)

def draw_finger_badge(frame, x, y, count):

    cv2.rectangle(frame, (x, y), (x + 120, y + 52), (15, 15, 25), -1)
    cv2.rectangle(frame, (x, y), (x + 120, y + 52), C_CYAN, 1)
    cv2.putText(frame, "JARI", (x + 8, y + 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_DIM, 1, cv2.LINE_AA)
    color = C_GREEN if count == 5 else C_CYAN
    cv2.putText(frame, str(count), (x + 14, y + 46),
                cv2.FONT_HERSHEY_DUPLEX, 1.2, color, 2, cv2.LINE_AA)

    for i in range(5):
        dot_c = color if i < count else C_DIM
        cv2.circle(frame, (x + 68 + i * 10, y + 30), 4, dot_c, -1)


def count_fingers(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    count = 0
    if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x:
        count += 1
    for i in range(1, 5):
        if hand_landmarks.landmark[tips[i]].y < hand_landmarks.landmark[tips[i] - 2].y:
            count += 1
    return count


def draw_hand_landmarks_custom(frame, hand_landmarks, w, h):
    connections = mp_hands.HAND_CONNECTIONS
    lms = hand_landmarks.landmark

    for conn in connections:
        x1c = int(lms[conn[0]].x * w)
        y1c = int(lms[conn[0]].y * h)
        x2c = int(lms[conn[1]].x * w)
        y2c = int(lms[conn[1]].y * h)
        cv2.line(frame, (x1c, y1c), (x2c, y2c), (0, 160, 80), 1)

    for i, lm in enumerate(lms):
        px, py = int(lm.x * w), int(lm.y * h)
        if i in [4, 8, 12, 16, 20]:  # fingertips
            cv2.circle(frame, (px, py), 6, C_ACCENT, -1)
            cv2.circle(frame, (px, py), 8, C_GREEN, 1)
        else:
            cv2.circle(frame, (px, py), 3, C_GREEN, -1)


tick = 0

while True:
    tick += 1


    if play_video:
        ret_vid, frame_vid = video.read()

        if not ret_vid:
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            play_video = False
            continue

        # # Letterbox overlay on video
        # h_v, w_v = frame_vid.shape[:2]
        # cv2.rectangle(frame_vid, (0, 0), (w_v, 36), (5, 5, 10), -1)
        # cv2.putText(frame_vid, "",
        #             (14, 24), cv2.FONT_HERSHEY_DUPLEX, 0.6, C_ACCENT, 1, cv2.LINE_AA)
        # cv2.rectangle(frame_vid, (0, h_v - 30), (w_v, h_v), (5, 5, 10), -1)
        # cv2.putText(frame_vid, "",
        #             (14, h_v - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_DIM, 1, cv2.LINE_AA)

        cv2.imshow("AI Scanner", frame_vid)
        key = cv2.waitKey(25)
        if key == 27:
            break
        continue

    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    box_x1, box_y1 = 180, 90
    box_x2, box_y2 = 460, 370

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    detected = False
    fingers = 0

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            draw_hand_landmarks_custom(frame, handLms, w, h)
            fingers = count_fingers(handLms)

            cx = int(handLms.landmark[9].x * w)
            cy = int(handLms.landmark[9].y * h)

            cv2.circle(frame, (cx, cy), 8, C_CYAN, -1)
            cv2.circle(frame, (cx, cy), 12, C_CYAN, 1)

            if box_x1 < cx < box_x2 and box_y1 < cy < box_y2:
                detected = True

    if detected and fingers == 5:
        if scan_start is None:
            scan_start = time.time()
        elapsed = time.time() - scan_start
        state = 'scanning'
        if elapsed >= scan_duration:
            play_video = True
            scan_start = None
            state = 'complete'
    elif detected:
        scan_start = None
        elapsed = 0
        state = 'ready'
    else:
        scan_start = None
        elapsed = 0
        state = 'idle'

    draw_status_bar(frame, w, h, tick)
    draw_scan_box(frame, box_x1, box_y1, box_x2, box_y2,
                  state, elapsed if detected else 0, scan_duration, tick)
    draw_bottom_bar(frame, w, h)

    if detected:
        draw_finger_badge(frame, w - 140, h - 110, fingers)

    # ── Instruction text (when idle)
    # if state == 'idle':
    #     msg = "Arahkan tangan ke dalam kotak"
    #     tw = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0][0]
    #     mx = (w - tw) // 2
    #     cv2.putText(frame, msg, (mx, box_y2 + 60),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_DIM, 1, cv2.LINE_AA)

    # elif state == 'ready':
    #     msg = "Buka semua 5 jari untuk mulai scan"
    #     tw = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0][0]
    #     mx = (w - tw) // 2
    #     cv2.putText(frame, msg, (mx, box_y2 + 60),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_YELLOW, 1, cv2.LINE_AA)

    cv2.imshow("AI Scanner", frame)

    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
video.release()
cv2.destroyAllWindows()