#include <WiFi.h>
#include <ESP32Servo.h>

const char* WIFI_SSID = "MOZAA";
const char* WIFI_PASS = "ANDRIAN02";
const int TCP_PORT = 8080;

Servo thumb;
Servo indexF;
Servo middle;
Servo ringF;
Servo pinky;

#define THUMB_PIN   2
#define INDEX_PIN   3
#define MIDDLE_PIN  4
#define RING_PIN    5
#define PINKY_PIN   10

const int THUMB_OPEN  = 90;
const int INDEX_OPEN  = 0;
const int MIDDLE_OPEN = 0;
const int RING_OPEN   = 0;
const int PINKY_OPEN  = 0;

WiFiServer server(TCP_PORT);
WiFiClient client;
unsigned long lastCmdTime = 0;
unsigned long lastWifiCheck = 0;
const unsigned long TIMEOUT_MS = 1000;
const unsigned long WIFI_CHECK_INTERVAL = 5000;

void setup() {
  Serial.begin(115200);

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  thumb.attach(THUMB_PIN);
  indexF.attach(INDEX_PIN);
  middle.attach(MIDDLE_PIN);
  ringF.attach(RING_PIN);
  pinky.attach(PINKY_PIN);
  openHand();

  connectWiFi();
  server.begin();
  Serial.printf("TCP server on port %d\n", TCP_PORT);
}

void loop() {
  if (millis() - lastWifiCheck > WIFI_CHECK_INTERVAL) {
    lastWifiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi lost! Reconnecting...");
      WiFi.disconnect();
      connectWiFi();
    }
  }

  if (WiFi.status() != WL_CONNECTED) {
    delay(100);
    return;
  }

  if (!client || !client.connected()) {
    client = server.available();
    if (client) {
      Serial.print("Client connected: ");
      Serial.println(client.remoteIP());
    }
    delay(10);
    return;
  }

  if (client.available() > 0) {
    String data = client.readStringUntil('\n');
    data.trim();
    if (data.length() == 0) return;

    int values[5];
    int idx = 0;
    char buf[64];
    data.toCharArray(buf, sizeof(buf));

    char *token = strtok(buf, ",");
    while (token != NULL && idx < 5) {
      values[idx] = constrain(atoi(token), 0, 180);
      idx++;
      token = strtok(NULL, ",");
    }

    if (idx == 5) {
      thumb.write(values[0]);
      indexF.write(values[1]);
      middle.write(values[2]);
      ringF.write(values[3]);
      pinky.write(values[4]);
      lastCmdTime = millis();
    }
  }

  if (millis() - lastCmdTime > TIMEOUT_MS && lastCmdTime != 0) {
    openHand();
    lastCmdTime = 0;
    Serial.println("Timeout - hand opened");
  }

  if (!client.connected()) {
    Serial.println("Client disconnected");
    client.stop();
  }

  delay(5);
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);

  Serial.println("\nScanning WiFi networks...");
  int n = WiFi.scanNetworks();
  if (n == 0) {
    Serial.println("No networks found!");
  } else {
    Serial.printf("Found %d networks:\n", n);
    for (int i = 0; i < n && i < 10; i++) {
      Serial.printf("  %s (%ddBm) %s\n",
        WiFi.SSID(i).c_str(),
        WiFi.RSSI(i),
        (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "OPEN" : "SECURE"
      );
    }
  }
  Serial.println();

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.printf("Connecting to \"%s\"", WIFI_SSID);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 60) {
    delay(500);
    Serial.print(".");
    attempts++;
    if (attempts % 10 == 0) {
      int s = WiFi.status();
      Serial.printf("\n  Status: %d ", s);
      switch (s) {
        case WL_NO_SSID_AVAIL: Serial.print("(SSID not found)"); break;
        case WL_CONNECT_FAILED: Serial.print("(Password wrong?)"); break;
        case WL_IDLE_STATUS: Serial.print("(Idle)"); break;
        case WL_DISCONNECTED: Serial.print("(Disconnected)"); break;
      }
    }
  }

  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
  } else {
    Serial.print("WiFi failed! Status: ");
    Serial.println(WiFi.status());
    Serial.println("Check: 1) SSID/password correct? 2) Is WiFi 2.4GHz? (ESP32 doesn't support 5GHz)");
    delay(5000);
    ESP.restart();
  }
}

void openHand() {
  thumb.write(THUMB_OPEN);
  indexF.write(INDEX_OPEN);
  middle.write(MIDDLE_OPEN);
  ringF.write(RING_OPEN);
  pinky.write(PINKY_OPEN);
}
