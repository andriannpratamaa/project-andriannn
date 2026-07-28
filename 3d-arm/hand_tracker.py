import cv2
import math
import time
import socket
import argparse
import numpy as np
import mediapipe as mp


SERVO_CONFIG = {
    'thumb':  {'open': 90, 'close': 40,  'mcp': 2, 'pip': 3, 'tip': 4},
    'index':  {'open': 0,  'close': 150, 'mcp': 5, 'pip': 6, 'tip': 8},
    'middle': {'open': 0,  'close': 160, 'mcp': 9, 'pip': 10, 'tip': 12},
    'ring':   {'open': 0,  'close': 120, 'mcp': 13, 'pip': 14, 'tip': 16},
    'pinky':  {'open': 0,  'close': 110, 'mcp': 17, 'pip': 18, 'tip': 20},
}

SERVO_NAMES = list(SERVO_CONFIG.keys())

SMOOTHING = 0.4
CHANGE_THRESHOLD = 2
SEND_INTERVAL = 0.05


def get_finger_curl(landmarks, mcp_id, pip_id, tip_id):
    mcp = landmarks[mcp_id]
    pip = landmarks[pip_id]
    tip = landmarks[tip_id]

    v1 = np.array([mcp.x - pip.x, mcp.y - pip.y])
    v2 = np.array([tip.x - pip.x, tip.y - pip.y])

    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm < 1e-6:
        return 0.0

    cos_angle = np.clip(dot / norm, -1.0, 1.0)
    angle = math.acos(cos_angle)
    return angle / math.pi


def map_servo(curl, open_angle, close_angle):
    curl = max(0.0, min(1.0, curl))
    return int(round(open_angle + curl * (close_angle - open_angle)))


class TcpClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = None
        self.connected = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3.0)
            self.sock.connect((self.ip, self.port))
            self.connected = True
            print(f"[OK] Connected to {self.ip}:{self.port}")
            return True
        except Exception as e:
            self.connected = False
            print(f"[WARN] Connection failed: {e}")
            return False

    def send(self, data):
        if not self.connected or not self.sock:
            return False
        try:
            self.sock.sendall(data.encode())
            return True
        except (BrokenPipeError, ConnectionResetError, OSError, AttributeError) as e:
            print(f"[WARN] Send failed: {e}")
            self.connected = False
            return False

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.connected = False


class HandTracker:
    def __init__(self, esp_ip="10.90.227.227", esp_port=8080):
        self.tcp = TcpClient(esp_ip, esp_port)
        self.tcp.connect()

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.smoothed = {name: 0.0 for name in SERVO_NAMES}
        self.last_sent = {name: -999 for name in SERVO_NAMES}
        self.last_send_time = 0
        self.last_reconnect = 0

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        angles = {name: None for name in SERVO_NAMES}

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )

                lm = hand_landmarks.landmark

                for name in SERVO_NAMES:
                    cfg = SERVO_CONFIG[name]
                    curl_raw = get_finger_curl(lm, cfg['mcp'], cfg['pip'], cfg['tip'])
                    curl_smooth = (
                        SMOOTHING * curl_raw + (1 - SMOOTHING) * self.smoothed[name]
                    )
                    self.smoothed[name] = curl_smooth
                    angles[name] = map_servo(curl_smooth, cfg['open'], cfg['close'])

        return angles

    def send_tcp(self, angles):
        now = time.time()
        if now - self.last_send_time < SEND_INTERVAL:
            return

        if not self.tcp.connected:
            if now - self.last_reconnect > 3:
                self.last_reconnect = now
                self.tcp.connect()
            return

        changed = False
        payload = []
        for name in SERVO_NAMES:
            a = angles[name] if angles[name] is not None else self.last_sent[name]
            if a is None:
                a = SERVO_CONFIG[name]['open']
            if abs(a - self.last_sent[name]) >= CHANGE_THRESHOLD:
                changed = True
            self.last_sent[name] = a
            payload.append(str(a))

        if changed:
            ok = self.tcp.send(','.join(payload) + '\n')
            if ok:
                self.last_send_time = now

    def draw_info(self, frame, angles, w, h):
        for i, name in enumerate(SERVO_NAMES):
            a = angles[name]
            label = f"{name}: {a}°" if a is not None else f"{name}: --"
            cv2.putText(
                frame, label, (10, 30 + i * 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 2,
            )

        status = f"TCP {'OK' if self.tcp.connected else '...retry'} | {self.tcp.ip}:{self.tcp.port}"
        color = (0, 255, 0) if self.tcp.connected else (0, 0, 255)
        cv2.putText(
            frame, status, (w - 300, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
        )

    def release(self):
        self.tcp.close()
        self.hands.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='10.90.227.227', help='ESP32 IP')
    parser.add_argument('--port', type=int, default=8080, help='ESP32 TCP port')
    parser.add_argument('--cam', '-c', type=int, default=0, help='Camera index')
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.cam)
    if not cap.isOpened():
        print("[ERR] Cannot open camera")
        return

    print(f"Target: {args.ip}:{args.port}")
    tracker = HandTracker(esp_ip=args.ip, esp_port=args.port)

    print("\n=== Hand Tracking Servo Arm (TCP/IP) ===")
    print("Press  Q / ESC  to exit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        angles = tracker.process(frame)

        if any(v is not None for v in angles.values()):
            tracker.send_tcp(angles)

        tracker.draw_info(frame, angles, w, h)
        cv2.imshow('Hand Tracking - 5 Servo Arm', frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break

    cap.release()
    tracker.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
