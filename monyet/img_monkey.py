import cv2
import mediapipe as mp
import numpy as np
import time

# === MediaPipe ===
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_detection
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

face = mp_face.FaceDetection(0.6)

# === Load Foto Monyet ===
monkey1 = cv2.imread("img/1.jpeg")
monkey2 = cv2.imread("img/2.jpeg")
monkey3 = cv2.imread("img/3.jpeg")   # default saat gesture tidak dikenali

current_monkey = monkey3
last_finger_state = -1
last_change_time = 0

# === Hitung jari ===
def count_fingers(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Ibu jari
    if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # 4 jari lainnya
    for tip in tips[1:]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return sum(fingers)


cap = cv2.VideoCapture(1)
prev_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # === Bikin kamera square (1:1) ===
    side = min(h, w)
    x0 = (w - side) // 2
    y0 = (h - side) // 2
    cam_square = frame[y0:y0+side, x0:x0+side]

    rgb = cv2.cvtColor(cam_square, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    face_result = face.process(rgb)

    h_sq, w_sq, _ = cam_square.shape

    # === Hitung FPS ===
    now = time.time()
    fps = 1 / (now - prev_time)
    prev_time = now

    finger_count = 0

    # =====================================================
    # === Skeleton Tangan + Lingkaran Telunjuk Besar ===
    # =====================================================
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:

            finger_count = count_fingers(hand_landmarks)

            # --- Gambar skeleton (warna kuning) ---
            mp_draw.draw_landmarks(
                cam_square,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=3),
                mp_draw.DrawingSpec(color=(0, 255, 255), thickness=2)
            )

            # --- Perbesar lingkaran pada ujung telunjuk (landmark 8) ---
            index_finger_tip = hand_landmarks.landmark[8]
            cx = int(index_finger_tip.x * w_sq)
            cy = int(index_finger_tip.y * h_sq)

            cv2.circle(cam_square, (cx, cy), 18, (0, 255, 255), -1)  # 18 px, kuning solid

    # === Delay 0,5 detik tiap kali ganti gambar ===
    current_time = time.time()
    if finger_count != last_finger_state and current_time - last_change_time >= 0.5:
        if finger_count == 1:
            current_monkey = monkey1
        elif finger_count == 2:
            current_monkey = monkey2
        else:
            current_monkey = monkey3

        last_finger_state = finger_count
        last_change_time = current_time

    # === Deteksi wajah ===
    if face_result.detections:
        for det in face_result.detections:
            box = det.location_data.relative_bounding_box
            x = int(box.xmin * w_sq)
            y = int(box.ymin * h_sq)
            bw = int(box.width * w_sq)
            bh = int(box.height * h_sq)
            cv2.rectangle(cam_square, (x, y), (x + bw, y + bh), (0, 255, 255), 2)

    # === Teks FPS + Kode Tangan ===
    cv2.putText(cam_square, f"FPS: {int(fps)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

    cv2.putText(cam_square, f"Hand Code: {finger_count}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)

    # === Resize monkey 1:1 ===
    mh, mw, _ = current_monkey.shape
    scale = min(w_sq / mw, h_sq / mh)
    new_w = int(mw * scale)
    new_h = int(mh * scale)

    monkey_resized = cv2.resize(current_monkey, (new_w, new_h))

    right_canvas = np.zeros((h_sq, w_sq, 3), dtype=np.uint8)
    x_off = (w_sq - new_w) // 2
    y_off = (h_sq - new_h) // 2
    right_canvas[y_off:y_off+new_h, x_off:x_off+new_w] = monkey_resized

    combined = np.hstack((cam_square, right_canvas))

    cv2.imshow("Gesture Monkey 1:1", combined)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
