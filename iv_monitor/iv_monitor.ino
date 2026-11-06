// IV bag monitor: weight, amount left and flow rate, a valve servo, a local page, and MQTT for the online dashboard.
// Libraries: "HX711 Arduino Library" (Bogdan Necula), "WiFiManager" (tzapu), "PubSubClient", from the Library Manager.
//
// Network:
//   First boot, or when the saved Wi-Fi cannot be found: the ESP32 opens "IV-Monitor-Setup" (password below).
//   Join it from a phone; the setup page lists the networks around and asks only for the router password.
//   The MQTT server is built in (below) and can be changed under "Setup" on that page, for advanced use.
//   Connected: the local page is at http://iv-monitor.local or at the IP printed on the Serial Monitor, and the device talks to MQTT.
//   Setup skipped or timed out: it runs on its own Wi-Fi "IV-Monitor" with the local page at http://192.168.4.1, as before.
//   To forget the saved Wi-Fi: send "wifi" on the Serial Monitor, or hold the tare button while powering on.
// Serial Monitor: 115200 baud, line ending "Newline".

#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <ESPmDNS.h>
#include <WiFiManager.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <HX711.h>
#include <Preferences.h>
#include <time.h>
#include "mbedtls/md.h"
#include <esp_task_wdt.h>
#include "soc/rtc_cntl_reg.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "page.h"

// Remote control over MQTT, for the GitHub Pages dashboard. The local page and the device's own Wi-Fi work either way.
#define USE_MQTT 1

// Screens, in screen.ino.
void screenMessage(const String &title, const String &a, const String &b = "", const String &c = "");
extern unsigned long screenHoldUntil;

const char *AP_SSID = "IV-Monitor";
const char *SETUP_SSID = "IV-Monitor";   // one name: the same network gives the setup page or the control page
const char *AP_PASS = "12345678";   // 8 characters or more, for both of the device's own networks
const int SETUP_TIMEOUT_S = 180;    // how long the setup page waits before the device goes on alone

// MQTT defaults, so a normal user only picks the Wi-Fi. Changeable under "Setup" on the setup page.
// The public broker needs no account, but anyone can read what is on it: commands are therefore signed with the control key.
const char *DEFAULT_MQTT_HOST = "broker.hivemq.com";
const char *DEFAULT_MQTT_PORT = "8883";
const int MQTT_FALLBACK_PORT = 1883;   // tried when a network blocks 8883; commands are still signed, readings travel unencrypted
const char *DEFAULT_CONTROL_KEY = "Wq7rT2kZ9pLm4xVb";   // the dashboard needs the same key; change it for your own device
const long long CMD_WINDOW_MS = 120000;                 // a signed command older than this is refused

const int PIN_DT = 18, PIN_SCK = 19;
const int PIN_SERVO = 32;
const int PIN_BUZZ = 25, PIN_GREEN = 26, PIN_RED = 27, PIN_TARE = 33;

const float STOPPED_MLH = 3;    // a rate under this, with fluid left and the valve open, means the flow stopped
const int WINDOW_S = 300;       // the rate is the slope over the last 5 minutes
const int MIN_WINDOW_S = 120;   // no rate until 2 minutes of readings
const float JUMP_G = 15;        // a step this big is a touch or a bag change
const int JUMP_HOLD_S = 10;     // a step that holds this long is a new bag
const int HIST_N = 60, HIST_EVERY_S = 5;   // chart: a point every 5 s, 5 minutes
const unsigned long MQTT_EVERY_MS = 2000;  // how often the state goes to MQTT

HX711 scale;
Preferences prefs;
WebServer server(80);
DNSServer dns;
WiFiClientSecure tlsClient;
WiFiClient plainClient;
PubSubClient mqtt;

// Settings, kept in the ESP32's flash.
float factor = 1, emptyBagG = 30, lowMl = 50, autoCloseMl = 0;
bool alertsOn = false;          // buzzer, red light and alert screens: off unless turned on from the page
long offset = 0;
int openDeg = 160, closeDeg = 135;   // closing turns 25 degrees counter-clockwise from open
char mqttHost[80] = "", mqttPort[6] = "", mqttUser[48] = "", mqttPass[64] = "", deviceId[24] = "", controlKey[40] = "";
long long lastCmdTs = 0;          // the newest signed command accepted, so an old one cannot be replayed

// Readings.
float hist[WINDOW_S];           // one reading a second, for the rate
int n = 0, head = 0;
float lastGood = NAN, pendingG = NAN;
int pendingS = 0;
float samples[7];               // raw samples between the once-a-second updates
int ns = 0, si = 0;
float chart[HIST_N];
int chartN = 0, chartHead = 0, chartTick = 0;

// What the pages show.
float curG = NAN, curMl = NAN, curRate = NAN;
int curMins = -1;
const char *curState = "warming";
int valveState = -1;            // -1 unknown, 0 open, 1 closed; kept across restarts
bool pageOpened = false;        // until someone opens the page, the screen shows its address
bool autoClosed = false;
bool onRouter = false;          // true: joined the router; false: running its own Wi-Fi
// Network health, published with the state so a drop can be explained afterwards.
int wifiDrops = 0, wifiWhy = 0;                // times the Wi-Fi dropped, and the last reason code
unsigned long wifiLostAt = 0;                  // when the Wi-Fi was lost, 0 while connected
const char *bootWhy = "";                      // why the board last started, e.g. power on, brownout

const char *resetName() {
  switch (esp_reset_reason()) {
    case ESP_RST_POWERON: return "power on";
    case ESP_RST_SW: return "restart";
    case ESP_RST_PANIC: return "crash";
    case ESP_RST_INT_WDT: case ESP_RST_TASK_WDT: case ESP_RST_WDT: return "watchdog";
    case ESP_RST_BROWNOUT: return "brownout";
    case ESP_RST_EXT: return "reset button";
    default: return "other";
  }
}
unsigned long servoOffAt = 0;

void save() {
  prefs.putFloat("factor", factor);
  prefs.putLong("offset", offset);
  prefs.putFloat("empty", emptyBagG);
  prefs.putFloat("low", lowMl);
  prefs.putFloat("auto", autoCloseMl);
  prefs.putInt("open", openDeg);
  prefs.putInt("close", closeDeg);
  prefs.putBool("alerts", alertsOn);
}

void saveMqtt() {
  prefs.putString("mHost", mqttHost);
  prefs.putString("mPort", mqttPort);
  prefs.putString("mUser", mqttUser);
  prefs.putString("mPass", mqttPass);
  prefs.putString("mId", deviceId);
  prefs.putString("mKey", controlKey);
}

void resetWindow() { n = 0; head = 0; }

void push(float g) {
  hist[head] = g;
  head = (head + 1) % WINDOW_S;
  if (n < WINDOW_S) n++;
}

// Least-squares slope of the stored readings, in grams per second.
float slope() {
  float sx = 0, sy = 0, sxx = 0, sxy = 0;
  for (int i = 0; i < n; i++) {
    float y = hist[(head - n + i + WINDOW_S) % WINDOW_S];
    sx += i; sy += y; sxx += (float)i * i; sxy += i * y;
  }
  float d = n * sxx - sx * sx;
  return d == 0 ? 0 : (n * sxy - sx * sy) / d;
}

// Take a sample only when the HX711 has one ready, so the web server is never kept waiting.
void sampleIfReady() {
  if (!scale.is_ready()) return;
  samples[si] = scale.get_units(1);
  si = (si + 1) % 7;
  if (ns < 7) ns++;
}

// Median of the recent samples, so a single bad sample does not count.
float median() {
  float v[7];
  for (int i = 0; i < ns; i++) v[i] = samples[i];
  for (int i = 1; i < ns; i++) {
    float t = v[i]; int j = i - 1;
    while (j >= 0 && v[j] > t) { v[j + 1] = v[j]; j--; }
    v[j + 1] = t;
  }
  return v[ns / 2];
}

void tare(const char *from) {
  screenMessage("Taring", "Keep the hook empty", "and still");
  scale.tare(20);
  offset = scale.get_offset();
  save();
  resetWindow();
  lastGood = NAN; ns = 0;
  Serial.printf("Tared from %s: the empty hook is now 0 g\n", from);
}

bool calibrate(float known) {
  if (known <= 0) return false;
  scale.set_scale(1);
  factor = scale.get_units(20) / known;
  scale.set_scale(factor);
  save();
  resetWindow();
  lastGood = NAN; ns = 0;
  Serial.printf("Calibrated: factor %.2f. The hook should now read about %.0f g\n", factor, known);
  return true;
}

// The servo's pulse, made directly on the PWM hardware: 50 per second, 0.5 to 2.4 ms for 0 to 180 degrees.
// Going straight to the target pulse, with no library start-up pulse, keeps it from twitching first.
const int SERVO_PUSH_MS = 600;   // how long it pushes before letting go, so it never keeps straining on the board
const uint32_t SERVO_FULL = 1 << 14;
void servoPulse(int us) { ledcWrite(PIN_SERVO, us ? (uint32_t)us * SERVO_FULL / 20000 : 0); }

// Move the servo, then let go of it: it stops pushing, and an idle servo makes no noise on the HX711.
void moveServo(int deg) {
  deg = constrain(deg, 0, 180);
  servoPulse(500 + deg * (2400 - 500) / 180);
  servoOffAt = millis() + SERVO_PUSH_MS;
  lastGood = NAN;
  resetWindow();
  Serial.printf("Servo at %d degrees\n", deg);
}

void setValve(bool close) {
  moveServo(close ? closeDeg : openDeg);
  valveState = close ? 1 : 0;
  prefs.putInt("valve", valveState);
  if (!close) autoClosed = false;
}

// Settings arrive as key=value pairs, from the local page or from MQTT.
void applySetting(const String &key, const String &val) {
  if (key == "emptyG") emptyBagG = constrain(val.toFloat(), 0, 500);
  else if (key == "lowMl") lowMl = constrain(val.toFloat(), 0, 1000);
  else if (key == "autoCloseMl") autoCloseMl = constrain(val.toFloat(), 0, 1000);
  else if (key == "openDeg") openDeg = constrain(val.toInt(), 0, 180);
  else if (key == "closeDeg") closeDeg = constrain(val.toInt(), 0, 180);
  else if (key == "alerts") alertsOn = val.toInt() != 0;
}

// Once a second: the reading, the amount left, the rate, the alerts and the chart.
void update() {
  if (ns == 0) return;
  float g = median();

  // A sudden step is ignored, unless it holds: then it is a new bag and the rate starts over.
  if (!isnan(lastGood) && fabsf(g - lastGood) > JUMP_G) {
    if (isnan(pendingG) || fabsf(g - pendingG) > JUMP_G) { pendingG = g; pendingS = 0; }
    if (++pendingS < JUMP_HOLD_S) { Serial.printf("%7.1f g  jump ignored\n", g); return; }
    resetWindow();
    Serial.println("New level held: rate restarted");
  }
  pendingG = NAN; pendingS = 0; lastGood = g;
  push(g);

  curG = g;
  curMl = fmaxf(0, g - emptyBagG);          // saline is about 1 g per ml
  bool haveRate = n >= MIN_WINDOW_S;
  curRate = haveRate ? fmaxf(0, -slope() * 3600) : NAN;   // ml per hour
  curMins = haveRate && curRate >= STOPPED_MLH ? (int)(curMl / curRate * 60) : -1;

  bool low = curMl <= lowMl;
  bool stopped = haveRate && curRate < STOPPED_MLH && !low && valveState != 1;
  if (autoCloseMl > 0 && curMl <= autoCloseMl && valveState != 1 && n >= 10) {
    setValve(true);
    autoClosed = true;
    Serial.printf("Closed by itself at %.0f ml\n", curMl);
  }
  curState = valveState == 1 ? "closed" : low ? "low" : stopped ? "stopped" : !haveRate ? "warming" : "ok";

  bool alert = alertsOn && (low || stopped) && valveState != 1;
  digitalWrite(PIN_GREEN, !alert);
  digitalWrite(PIN_RED, alert);
  static bool beep = false;
  beep = alert && !beep;
  digitalWrite(PIN_BUZZ, beep);

  if (++chartTick >= HIST_EVERY_S) {
    chartTick = 0;
    chart[chartHead] = g;
    chartHead = (chartHead + 1) % HIST_N;
    if (chartN < HIST_N) chartN++;
  }

  Serial.printf("%7.1f g  %5.0f ml  ", g, curMl);
  if (!haveRate) Serial.printf("rate in %d s\n", MIN_WINDOW_S - n);
  else Serial.printf("%6.1f ml/h  %s\n", curRate, curState);
}

void num(String &s, const char *key, float v, int dec) {
  s += '"'; s += key; s += "\":";
  if (isnan(v)) s += "null"; else s += String(v, dec);
  s += ',';
}

String stateJson() {
  String s;
  s.reserve(1400);
  s += '{';
  num(s, "g", curG, 1);
  num(s, "ml", curMl, 0);
  num(s, "rate", curRate, 1);
  num(s, "mins", curMins < 0 ? NAN : curMins, 0);
  num(s, "emptyG", emptyBagG, 0);
  num(s, "lowMl", lowMl, 0);
  num(s, "autoCloseMl", autoCloseMl, 0);
  s += "\"alerts\":"; s += alertsOn ? "true" : "false"; s += ',';
  num(s, "openDeg", openDeg, 0);
  num(s, "closeDeg", closeDeg, 0);
  num(s, "rateIn", n >= MIN_WINDOW_S ? 0 : MIN_WINDOW_S - n, 0);
  s += "\"state\":\""; s += curState; s += "\",";
  s += "\"valve\":\""; s += valveState == 1 ? "closed" : valveState == 0 ? "open" : "unknown"; s += "\",";
  s += "\"autoClosed\":"; s += autoClosed ? "true" : "false"; s += ',';
  s += "\"mqtt\":"; s += mqtt.connected() ? "true" : "false"; s += ',';
  s += "\"id\":\""; s += deviceId; s += "\",";
  s += "\"ssid\":\""; s += WiFi.status() == WL_CONNECTED ? WiFi.SSID() : String(""); s += "\",";
  s += "\"ip\":\""; s += WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : String(""); s += "\",";
  num(s, "rssi", WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : NAN, 0);
  num(s, "drops", wifiDrops, 0);
  num(s, "why", wifiWhy, 0);
  num(s, "up", millis() / 1000, 0);
  s += "\"boot\":\""; s += bootWhy; s += "\",";
  s += "\"chart\":[";
  for (int i = 0; i < chartN; i++) {
    if (i) s += ',';
    s += String(chart[(chartHead - chartN + i + HIST_N) % HIST_N], 1);
  }
  s += "]}";
  return s;
}

void sendState() {
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", stateJson());
}

// ---------- MQTT ----------

String topic(const char *leaf) { return String("ivmon/") + deviceId + "/" + leaf; }

void publishState() {
  if (!mqtt.connected()) return;
  String s = stateJson();
  mqtt.publish(topic("state").c_str(), s.c_str(), true);
}

String hmacHex(const String &msg) {
  unsigned char out[32];
  mbedtls_md_hmac(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), (const unsigned char *)controlKey, strlen(controlKey),
                  (const unsigned char *)msg.c_str(), msg.length(), out);
  char hex[65];
  for (int i = 0; i < 32; i++) sprintf(hex + 2 * i, "%02x", out[i]);
  return String(hex);
}

// Commands on ivmon/<device>/cmd, signed: "<time in ms>|<command>|<HMAC-SHA256 of time|command, hex>".
// Commands: open, close, tare, cal 500, servo 90, set emptyG=38&lowMl=50
void onMqtt(char *t, byte *payload, unsigned int len) {
  String msg;
  msg.reserve(len);
  for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
  int a = msg.indexOf('|'), b = msg.lastIndexOf('|');
  if (a < 0 || b <= a) { mqtt.publish(topic("ack").c_str(), "error: unsigned command"); return; }
  long long ts = strtoll(msg.substring(0, a).c_str(), nullptr, 10);
  String cmd = msg.substring(a + 1, b);
  if (!msg.substring(b + 1).equalsIgnoreCase(hmacHex(msg.substring(0, b)))) {
    Serial.println("MQTT: command with a wrong signature ignored");
    mqtt.publish(topic("ack").c_str(), "error: wrong control key");
    return;
  }
  long long now = (long long)time(nullptr) * 1000;
  bool clockSet = now > 1700000000000LL;
  if (ts <= lastCmdTs || (clockSet && llabs(now - ts) > CMD_WINDOW_MS)) {
    mqtt.publish(topic("ack").c_str(), "error: command too old");
    return;
  }
  lastCmdTs = ts;
  cmd.trim();
  Serial.printf("MQTT command: %s\n", cmd.c_str());
  String ack = "ok " + cmd;
  if (cmd == "open") setValve(false);
  else if (cmd == "close") setValve(true);
  else if (cmd == "tare") tare("MQTT");
  else if (cmd.startsWith("cal ")) { if (!calibrate(cmd.substring(4).toFloat())) ack = "error: cal needs a weight in grams"; }
  else if (cmd.startsWith("servo ")) { moveServo(cmd.substring(6).toInt()); valveState = -1; }
  else if (cmd.startsWith("set ")) {
    String rest = cmd.substring(4);
    while (rest.length()) {
      int amp = rest.indexOf('&');
      String pair = amp < 0 ? rest : rest.substring(0, amp);
      rest = amp < 0 ? "" : rest.substring(amp + 1);
      int eq = pair.indexOf('=');
      if (eq > 0) applySetting(pair.substring(0, eq), pair.substring(eq + 1));
    }
    save();
  } else ack = "error: unknown command";
  mqtt.publish(topic("ack").c_str(), ack.c_str());
  publishState();
}

int mqttPortNow = 0;   // the port in use: the saved one, or the fallback after failures

void mqttUsePort(int port) {
  mqttPortNow = port;
  if (port == 8883) {
    tlsClient.setInsecure();   // encrypted, but the broker's certificate is not checked: fine for a test, not for a ward
    tlsClient.setHandshakeTimeout(5);   // a stalled handshake must not freeze the screen and the scale
    tlsClient.setTimeout(5000);
    mqtt.setClient(tlsClient);
  } else {
    plainClient.setTimeout(5000);
    mqtt.setClient(plainClient);
  }
  mqtt.setServer(mqttHost, port);
}

void setupMqtt() {
  if (!mqttHost[0]) { Serial.println("MQTT: no broker set, skipping"); return; }
  mqttUsePort(atoi(mqttPort));
  mqtt.setBufferSize(2048);
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(5);
  mqtt.setCallback(onMqtt);
}

void mqttLoop() {
  if (!onRouter || !mqttHost[0] || WiFi.status() != WL_CONNECTED) return;
  if (!mqtt.connected()) {
    // A blocked network makes every attempt hang for a few seconds, so wait longer after each failure (10 s up to 2 min).
    static unsigned long lastTry = 0, gap = 0;
    static int fails = 0;
    if (lastTry && millis() - lastTry < gap) return;
    lastTry = millis();
    String clientId = String("ivmon-") + deviceId + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    String status = topic("status");
    Serial.printf("MQTT: connecting to %s:%d ... ", mqttHost, mqttPortNow);
    if (mqtt.connect(clientId.c_str(), mqttUser[0] ? mqttUser : nullptr, mqttPass[0] ? mqttPass : nullptr, status.c_str(), 1, true, "offline")) {
      Serial.printf("connected on %d\n", mqttPortNow);
      fails = 0;
      gap = 10000;
      mqtt.publish(status.c_str(), "online", true);
      mqtt.subscribe(topic("cmd").c_str(), 1);
      publishState();
    } else {
      fails++;
      gap = min(10000UL << min(fails - 1, 4), 120000UL);
      // Two failures in a row on one port: try the other (8883 and 1883 in turn).
      int saved = atoi(mqttPort);
      if (fails % 2 == 0 && saved != MQTT_FALLBACK_PORT) mqttUsePort(mqttPortNow == saved ? MQTT_FALLBACK_PORT : saved);
      Serial.printf("failed (state %d), next try on %d in %lu s\n", mqtt.state(), mqttPortNow, gap / 1000);
    }
    return;
  }
  mqtt.loop();
  static unsigned long lastPub = 0;
  if (millis() - lastPub >= MQTT_EVERY_MS) { lastPub = millis(); publishState(); }
}

// ---------- Wi-Fi and the local page ----------

// Once on a router: the clock (for signed commands) and the iv-monitor.local name.
void routerUp() {
  WiFi.setSleep(false);
  configTime(0, 0, "pool.ntp.org", "time.google.com");   // the clock lets old signed commands be refused
  MDNS.end();
  if (MDNS.begin("iv-monitor")) MDNS.addService("http", "tcp", 80);
  Serial.printf("On the router \"%s\". Local page: http://iv-monitor.local or http://%s\n", WiFi.SSID().c_str(), WiFi.localIP().toString().c_str());
}

// The device's own Wi-Fi, always on next to the router: a phone that joins it opens 192.168.4.1, anywhere.
void ownWifiOn() {
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASS);
  dns.start(53, "*", WiFi.softAPIP());   // any address the phone asks for leads to the page
  Serial.printf("Own Wi-Fi \"%s\" on: http://%s\n", AP_SSID, WiFi.softAPIP().toString().c_str());
}

void setupNetwork(bool forgetWifi, bool openSetup) {
  WiFiManager wm;
  if (forgetWifi) { wm.resetSettings(); Serial.println("Saved Wi-Fi forgotten"); }

  // Advanced settings, on their own "Setup" page: the Wi-Fi page asks only for the network and its password.
  WiFiManagerParameter pNote("<p><b>Advanced settings.</b> Leave them as they are unless you run your own MQTT server.</p>");
  WiFiManagerParameter pHost("mhost", "MQTT server", mqttHost, sizeof(mqttHost) - 1);
  WiFiManagerParameter pPort("mport", "MQTT port (8883 = TLS)", mqttPort, sizeof(mqttPort) - 1);
  WiFiManagerParameter pUser("muser", "MQTT username (empty for the public server)", mqttUser, sizeof(mqttUser) - 1);
  WiFiManagerParameter pPass("mpass", "MQTT password", mqttPass, sizeof(mqttPass) - 1, "type=\"password\"");
  WiFiManagerParameter pId("mid", "Device name", deviceId, sizeof(deviceId) - 1);
  WiFiManagerParameter pKey("mkey", "Control key (the dashboard needs the same)", controlKey, sizeof(controlKey) - 1);
  if (USE_MQTT) {
    wm.addParameter(&pNote);
    wm.addParameter(&pHost);
    wm.addParameter(&pPort);
    wm.addParameter(&pUser);
    wm.addParameter(&pPass);
    wm.addParameter(&pId);
    wm.addParameter(&pKey);
    wm.setParamsPage(true);
  }
  std::vector<const char *> menu = USE_MQTT ? std::vector<const char *>{ "wifi", "param", "info", "exit" }
                                            : std::vector<const char *>{ "wifi", "info", "exit" };
  wm.setMenu(menu);
  wm.setTitle("IV Monitor");
  wm.setConfigPortalTimeout(SETUP_TIMEOUT_S);
  wm.setConnectTimeout(20);

  wm.setAPCallback([](WiFiManager *) { screenSetup(); });
  screenConnecting(wm.getWiFiIsSaved() ? wm.getWiFiSSID() : String(""));
  Serial.printf("Joining the saved Wi-Fi, or opening \"%s\" for setup (%d s)...\n", SETUP_SSID, SETUP_TIMEOUT_S);
  onRouter = openSetup ? wm.startConfigPortal(SETUP_SSID, AP_PASS) : wm.autoConnect(SETUP_SSID, AP_PASS);

  // Keep what was typed on the setup page, even when the Wi-Fi part did not work out.
  if (strcmp(pHost.getValue(), mqttHost) || strcmp(pPort.getValue(), mqttPort) || strcmp(pUser.getValue(), mqttUser) ||
      strcmp(pPass.getValue(), mqttPass) || strcmp(pId.getValue(), deviceId) || strcmp(pKey.getValue(), controlKey)) {
    if (pHost.getValue()[0]) strlcpy(mqttHost, pHost.getValue(), sizeof(mqttHost));
    if (pPort.getValue()[0]) strlcpy(mqttPort, pPort.getValue(), sizeof(mqttPort));
    strlcpy(mqttUser, pUser.getValue(), sizeof(mqttUser));
    strlcpy(mqttPass, pPass.getValue(), sizeof(mqttPass));
    if (pId.getValue()[0]) strlcpy(deviceId, pId.getValue(), sizeof(deviceId));
    if (pKey.getValue()[0]) strlcpy(controlKey, pKey.getValue(), sizeof(controlKey));
    saveMqtt();
  }

  ownWifiOn();
  if (onRouter) routerUp();
  else Serial.println("No router yet: it keeps looking for the saved one in the background");
  screenNetResult();
}

void setupWeb() {
  server.on("/", []() { server.send(200, "text/html; charset=utf-8", PAGE); });
  server.on("/api/state", []() { pageOpened = true; sendState(); });
  server.on("/api/valve", HTTP_POST, []() {
    String to = server.arg("to");
    if (to == "open") setValve(false);
    else if (to == "close") setValve(true);
    else { server.send(400, "text/plain", "to must be open or close"); return; }
    sendState();
  });
  // Correct the recorded state when it is wrong (the valve was moved by hand), without moving the servo.
  server.on("/api/valvestate", HTTP_POST, []() {
    String is = server.arg("is");
    if (is == "open") valveState = 0;
    else if (is == "closed") valveState = 1;
    else { server.send(400, "text/plain", "is must be open or closed"); return; }
    autoClosed = false;
    prefs.putInt("valve", valveState);
    sendState();
  });
  // Set up a different Wi-Fi: restart into the setup page on the device's own network.
  server.on("/api/wifisetup", HTTP_POST, []() {
    server.send(200, "text/plain", "restarting into setup");
    prefs.putBool("setup", true);
    delay(300);
    ESP.restart();
  });
  server.on("/api/tare", HTTP_POST, []() { tare("the web page"); sendState(); });
  server.on("/api/servo", HTTP_POST, []() {
    if (!server.hasArg("deg")) { server.send(400, "text/plain", "deg is missing"); return; }
    moveServo(server.arg("deg").toInt());
    valveState = -1;
    sendState();
  });
  server.on("/api/cal", HTTP_POST, []() {
    if (!calibrate(server.arg("g").toFloat())) { server.send(400, "text/plain", "g must be a weight in grams"); return; }
    sendState();
  });
  server.on("/api/set", HTTP_POST, []() {
    for (const char *k : { "emptyG", "lowMl", "autoCloseMl", "openDeg", "closeDeg", "alerts" })
      if (server.hasArg(k)) applySetting(k, server.arg(k));
    save();
    sendState();
  });
  server.onNotFound([]() {
    if (server.client().localIP() != WiFi.softAPIP()) { server.send(404, "text/plain", "Not found"); return; }
    server.sendHeader("Location", "http://192.168.4.1/", true);
    server.send(302, "text/plain", "");
  });
  server.begin();
}

void commands() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line == "t") {
    tare("the Serial Monitor");
  } else if (line.startsWith("c ")) {
    if (!calibrate(line.substring(2).toFloat())) Serial.println("Write the known weight in grams, e.g. c 500");
  } else if (line.startsWith("e ")) {
    emptyBagG = line.substring(2).toFloat();
    save();
    Serial.printf("Empty bag and tubing set to %.0f g\n", emptyBagG);
  } else if (line == "r") {
    resetWindow();
    Serial.println("Rate restarted");
  } else if (line.startsWith("a ")) {
    moveServo(line.substring(2).toInt());
  } else if (line == "o" || line == "x") {
    setValve(line == "x");
  } else if (line.startsWith("so ") || line.startsWith("sc ")) {
    int deg = constrain(line.substring(3).toInt(), 0, 180);
    if (line[1] == 'o') openDeg = deg; else closeDeg = deg;
    save();
    Serial.printf("Open at %d degrees, close at %d degrees\n", openDeg, closeDeg);
  } else if (line == "wifi") {
    WiFiManager().resetSettings();
    Serial.println("Saved Wi-Fi forgotten. Restarting into setup...");
    delay(500);
    ESP.restart();
  } else if (line == "i2c") {
    i2cScan();
  } else if (line == "net") {
    Serial.printf("Wi-Fi \"%s\" (%s), signal %d dBm, %d drops (last reason %d), started after %s, up %lu s\n",
                  WiFi.SSID().c_str(), WiFi.BSSIDstr().c_str(), WiFi.RSSI(), wifiDrops, wifiWhy, bootWhy, millis() / 1000);
    Serial.printf("Router IP %s, own Wi-Fi %s (%d joined), MQTT %s (%s:%d, device %s)\n",
                  WiFi.localIP().toString().c_str(), WiFi.softAPIP().toString().c_str(), WiFi.softAPgetStationNum(),
                  mqtt.connected() ? "connected" : "not connected", mqttHost, mqttPortNow, deviceId);
  } else {
    Serial.println("Commands: t = tare (hook empty), c 500 = calibrate with 500 g on the hook, e 30 = empty bag weight in g, r = restart the rate, a 90 = servo to 90 degrees, o = open, x = close, so 180 / sc 90 = set the open / close angle, net = network status, wifi = forget the Wi-Fi");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUZZ, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_TARE, INPUT_PULLUP);
  ledcAttach(PIN_SERVO, 50, 14);
  servoPulse(0);   // no pulse: the servo stays where it is

  prefs.begin("iv", false);
  factor = prefs.getFloat("factor", 1);
  offset = prefs.getLong("offset", 0);
  emptyBagG = prefs.getFloat("empty", 30);
  lowMl = prefs.getFloat("low", 50);
  autoCloseMl = prefs.getFloat("auto", 0);
  alertsOn = prefs.getBool("alerts", false);
  openDeg = prefs.getInt("open", 160);
  closeDeg = prefs.getInt("close", 135);
  prefs.getString("mHost", mqttHost, sizeof(mqttHost));
  prefs.getString("mPort", mqttPort, sizeof(mqttPort));
  prefs.getString("mUser", mqttUser, sizeof(mqttUser));
  prefs.getString("mPass", mqttPass, sizeof(mqttPass));
  prefs.getString("mId", deviceId, sizeof(deviceId));
  prefs.getString("mKey", controlKey, sizeof(controlKey));
  if (!mqttHost[0]) strlcpy(mqttHost, DEFAULT_MQTT_HOST, sizeof(mqttHost));
  if (!mqttPort[0]) strlcpy(mqttPort, DEFAULT_MQTT_PORT, sizeof(mqttPort));
  if (!controlKey[0]) strlcpy(controlKey, DEFAULT_CONTROL_KEY, sizeof(controlKey));
  if (!deviceId[0]) snprintf(deviceId, sizeof(deviceId), "iv-%06lx", (unsigned long)((ESP.getEfuseMac() >> 24) & 0xffffff));

  scale.begin(PIN_DT, PIN_SCK);
  scale.set_scale(factor);
  scale.set_offset(offset);

  screenBegin();
  screenBoot();

  Serial.println("\nSend any letter for the list of commands.");
  if (factor == 1) Serial.println("Not calibrated yet: send t with the hook empty, then hang a known weight and send c <grams>");

  bool forget = digitalRead(PIN_TARE) == LOW;   // tare button held at power-on: forget the Wi-Fi
  bootWhy = resetName();
  Serial.printf("Started after: %s\n", bootWhy);
  WiFi.onEvent([](WiFiEvent_t, WiFiEventInfo_t info) {
    wifiDrops++;
    wifiWhy = info.wifi_sta_disconnected.reason;
    if (!wifiLostAt) wifiLostAt = millis() | 1;
    Serial.printf("Wi-Fi lost (reason %d)\n", wifiWhy);
  }, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

  bool openSetup = prefs.getBool("setup", false);   // asked for from the page
  if (openSetup) prefs.putBool("setup", false);
  // Starting the radio draws a short burst of current that a weak USB port cannot give: the voltage dips and the
  // brownout guard restarts the chip, over and over. The guard is off only while the radio starts, then back on.
  uint32_t brownout = READ_PERI_REG(RTC_CNTL_BROWN_OUT_REG);
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  setupNetwork(forget, openSetup);
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, brownout);
  wifiDrops = 0;   // drops while joining at start do not count
  setupWeb();
  if (USE_MQTT) setupMqtt();

  // The valve as it was left; the servo is not moved at start.
  valveState = prefs.getInt("valve", -1);

  // If the loop ever stops for 30 s, restart rather than sit frozen on the last screen.
  esp_task_wdt_config_t wdt = { .timeout_ms = 30000, .idle_core_mask = 0, .trigger_panic = true };
  esp_task_wdt_reconfigure(&wdt);
  esp_task_wdt_add(NULL);
}

// Keep looking for the saved router, whether it dropped or was never found at start.
// Searching moves the radio across channels and upsets a phone on the device's own Wi-Fi, so it searches less often while one is joined.
// Restarts only when the router was lost for 3 minutes and nobody is on the device's own Wi-Fi.
void wifiWatch() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!onRouter) { onRouter = true; routerUp(); }
    if (wifiLostAt) { Serial.printf("Wi-Fi back, %s\n", WiFi.localIP().toString().c_str()); wifiLostAt = 0; }
    return;
  }
  static bool saved = WiFiManager().getWiFiIsSaved();
  if (!saved) return;
  if (!wifiLostAt) wifiLostAt = millis() | 1;
  int guests = WiFi.softAPgetStationNum();
  static unsigned long lastTry = 0;
  if (millis() - lastTry > (guests ? 60000UL : 15000UL)) {
    lastTry = millis();
    Serial.println("Wi-Fi: looking for the router");
    if (onRouter) WiFi.reconnect(); else WiFi.begin();
  }
  if (onRouter && !guests && millis() - wifiLostAt > 180000) { Serial.println("Wi-Fi away for 3 minutes: restarting"); delay(100); ESP.restart(); }
}

void loop() {
  esp_task_wdt_reset();
  wifiWatch();
  dns.processNextRequest();
  server.handleClient();
  if (USE_MQTT) mqttLoop();
  commands();
  sampleIfReady();

  if (servoOffAt && millis() > servoOffAt) { servoPulse(0); servoOffAt = 0; }

  if (digitalRead(PIN_TARE) == LOW) {
    delay(30);
    if (digitalRead(PIN_TARE) == LOW) {
      tare("the button");
      unsigned long held = millis();   // wait for release, but never hang on a stuck button
      while (digitalRead(PIN_TARE) == LOW && millis() - held < 5000) delay(10);
    }
  }

  static unsigned long next = 0;
  if (millis() >= next) {
    next = millis() + 1000;
    update();
  }

  static unsigned long nextScreen = 0;
  if (millis() >= nextScreen && millis() >= screenHoldUntil) {
    nextScreen = millis() + 500;
    screenDraw();
  }
}
