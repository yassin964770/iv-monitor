// The 0.96 in OLED (SSD1306, 128 x 64) on I2C: SDA on GPIO 21, SCL on GPIO 22, VCC on 3V3.
// Mounted upright: the picture is turned 90 degrees clockwise, so it is 64 wide and 128 tall.
// Every screen says what is happening and, when the user has something to do, what to do.

const int OLED_W = 128, OLED_H = 64;   // the panel as made
const int ROTATION = 1;                // 1 = 90 degrees clockwise; 3 turns it the other way
const int W = 64, H = 128;             // the picture as seen, after turning
const int LINE_CHARS = W / 6;          // 10 characters across at the small size

// The clock used while drawing is set below, after checking the wiring can carry it.
Adafruit_SSD1306 *oledP = nullptr;
#define oled (*oledP)
bool oledOk = false;
unsigned long screenHoldUntil = 0;   // a message stays up until then before the main screen returns

// True when a device answers at addr, trying a few times (loose jumper wires drop the odd reply).
bool i2cAnswers(uint8_t addr) {
  for (int i = 0; i < 3; i++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) return true;
    delay(5);
  }
  return false;
}

void screenBegin() {
  oledOk = false;
  Wire.begin(21, 22);
  Wire.setClock(100000);
  uint8_t addr = 0;
  for (uint8_t a : { 0x3C, 0x3D }) if (i2cAnswers(a)) { addr = a; break; }
  if (!addr) { Serial.println("OLED not found: check SDA on 21, SCL on 22, VCC on 3V3, GND"); return; }

  // Fast clock only if the wires answer reliably at it; otherwise stay slow.
  Wire.setClock(400000);
  uint32_t clk = i2cAnswers(addr) ? 400000 : 100000;
  Wire.setClock(clk);
  if (!oledP) oledP = new Adafruit_SSD1306(OLED_W, OLED_H, &Wire, -1, clk, clk);
  if (!oled.begin(SSD1306_SWITCHCAPVCC, addr, true, false)) { Serial.println("OLED: not enough memory"); return; }
  oledOk = true;
  Serial.printf("OLED found at 0x%02X, I2C at %u kHz\n", addr, clk / 1000);
  oled.setRotation(ROTATION);
  oled.setTextColor(SSD1306_WHITE);
  oled.cp437(true);
  oled.setTextWrap(false);
}

// Wiring check: lists every I2C device with SDA/SCL as wired, then swapped, and retries the screen.
void i2cScan() {
  for (int swap = 0; swap < 2; swap++) {
    int sda = swap ? 22 : 21, scl = swap ? 21 : 22, found = 0;
    Wire.end();
    Wire.begin(sda, scl);
    Serial.printf("I2C with SDA on %d, SCL on %d:", sda, scl);
    for (uint8_t a = 8; a < 120; a++) {
      Wire.beginTransmission(a);
      if (Wire.endTransmission() == 0) { Serial.printf(" 0x%02X", a); found++; }
    }
    Serial.println(found ? "" : " nothing");
  }
  Wire.end();
  screenBegin();
}

// Text centred across the width.
void centred(const String &s, int y, int size) {
  oled.setTextSize(size);
  int x = (W - (int)s.length() * 6 * size) / 2;
  oled.setCursor(x < 0 ? 0 : x, y);
  oled.print(s);
}

// The largest text size (3, 2 or 1) at which s fits across the width.
int fitSize(const String &s, int most = 3) {
  for (int size = most; size > 1; size--)
    if ((int)s.length() * 6 * size <= W) return size;
  return 1;
}

// Small text wrapped at spaces to the width, each line centred; long words are cut.
// Returns the y under the last line.
int wrapped(const String &s, int y) {
  String rest = s;
  rest.trim();
  while (rest.length()) {
    int cut = rest.length();
    if (cut > LINE_CHARS) {
      cut = rest.lastIndexOf(' ', LINE_CHARS);
      if (cut <= 0) cut = LINE_CHARS;
    }
    centred(rest.substring(0, cut), y, 1);
    rest = rest.substring(cut);
    rest.trim();
    y += 10;
  }
  return y;
}

// A titled message: a bar across the top, then up to three short texts, each wrapped.
void screenMessage(const String &title, const String &a, const String &b, const String &c) {
  if (!oledOk) return;
  oled.clearDisplay();
  oled.fillRect(0, 0, W, 13, SSD1306_WHITE);
  oled.setTextColor(SSD1306_BLACK);
  centred(title.length() > LINE_CHARS ? title.substring(0, LINE_CHARS) : title, 3, 1);
  oled.setTextColor(SSD1306_WHITE);
  int y = 22;
  for (const String *s : { &a, &b, &c })
    if (s->length()) y = wrapped(*s, y) + 6;
  oled.display();
}

void screenBoot() {
  if (!oledOk) return;
  oled.clearDisplay();
  centred("IV", 30, 3);
  centred("Monitor", 60, 1);
  centred("Starting...", 96, 1);
  oled.display();
}

void screenConnecting(const String &ssid) {
  screenMessage("Wi-Fi", "Connecting to", ssid.length() ? ssid : String("saved network"), "please wait");
}

void screenSetup() {
  screenMessage("Setup", String("Join ") + SETUP_SSID, String("Pass ") + AP_PASS, "Open 192.168.4.1");
}

void screenNetResult() {
  screenHoldUntil = millis() + 4000;
  if (onRouter) screenMessage("Connected", WiFi.SSID(), WiFi.localIP().toString(), String("also ") + AP_SSID);
  else screenMessage("No router", String("Wi-Fi ") + AP_SSID, String("Pass ") + AP_PASS, "Open 192.168.4.1");
}

// Top row: Wi-Fi bars (or "AP" on its own network), a cloud when MQTT is up, the weight on the right.
void statusBar() {
  oled.setTextSize(1);
  if (onRouter && WiFi.status() == WL_CONNECTED) {
    int rssi = WiFi.RSSI(), bars = rssi > -60 ? 3 : rssi > -72 ? 2 : 1;
    for (int i = 0; i < 3; i++) {
      int h = 3 + i * 2;
      if (i < bars) oled.fillRect(i * 4, 7 - h, 3, h, SSD1306_WHITE);
      else oled.drawRect(i * 4, 7 - h, 3, h, SSD1306_WHITE);
    }
  } else if (onRouter) {   // lost the router: say so plainly, the weight can wait
    oled.fillRect(0, 0, W, 10, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK);
    centred("NO WI-FI", 1, 1);
    oled.setTextColor(SSD1306_WHITE);
    return;
  } else {
    oled.setCursor(0, 0);
    oled.print("AP");
  }
  if (!USE_MQTT) {
  } else if (mqtt.connected()) {   // a small cloud: filled when online, an outline with a gap when not
    oled.fillCircle(17, 4, 2, SSD1306_WHITE);
    oled.fillCircle(21, 3, 3, SSD1306_WHITE);
    oled.fillCircle(25, 4, 2, SSD1306_WHITE);
    oled.fillRect(17, 4, 9, 3, SSD1306_WHITE);
  } else if (onRouter) {
    oled.drawCircle(17, 4, 2, SSD1306_WHITE);
    oled.drawCircle(21, 3, 3, SSD1306_WHITE);
    oled.drawCircle(25, 4, 2, SSD1306_WHITE);
    oled.drawLine(15, 8, 27, 0, SSD1306_WHITE);
  }
  String g = String((int)roundf(curG)) + "g";
  oled.setCursor(W - g.length() * 6, 0);
  oled.print(g);
  oled.drawFastHLine(0, 10, W, SSD1306_WHITE);
}

// Bottom band: the valve. Closed is filled white, so it reads at a glance.
void valveBand() {
  const int y = 115;
  String v = valveState == 1 ? (autoClosed ? "AUTO CLOSE" : "CLOSED") : valveState == 0 ? "OPEN" : "VALVE ?";
  if (valveState == 1) {
    oled.fillRect(0, y, W, H - y, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK);
  } else {
    oled.drawRect(0, y, W, H - y, SSD1306_WHITE);
  }
  centred(v, y + 3, 1);
  oled.setTextColor(SSD1306_WHITE);
}

// Where to open the page, shown until someone does. Each part of the address on its own large line.
void screenAddress() {
  oled.clearDisplay();
  oled.fillRect(0, 0, W, 13, SSD1306_WHITE);
  oled.setTextColor(SSD1306_BLACK);
  centred("OPEN PAGE", 3, 1);
  oled.setTextColor(SSD1306_WHITE);
  // On a router: its address and the device's own Wi-Fi in turn, 5 s each. Either one opens the same page.
  bool router = onRouter && WiFi.status() == WL_CONNECTED && (millis() / 5000) % 2 == 0;
  String ip;
  if (router) {
    ip = WiFi.localIP().toString();
    centred("in browser", 17, 1);   // 10 characters: the most that fit across
  } else {
    ip = WiFi.softAPIP().toString();
    centred(AP_SSID, 17, 1);           // the network to join; "Join IV-Monitor" would not fit
  }
  int y = 30;
  while (ip.length()) {
    int dot = ip.indexOf('.');
    String part = dot < 0 ? ip : ip.substring(0, dot + 1);
    ip = dot < 0 ? "" : ip.substring(dot + 1);
    centred(part, y, 2);
    y += 18;
  }
  if (router) { centred("iv-monitor", 104, 1); centred(".local", 114, 1); }
  else wrapped(String("Pass ") + AP_PASS, 104);
  oled.display();
}

// Alerts take the whole screen and blink, to be seen from across the room.
// Each word of `big` goes on its own line, as large as fits.
void alertScreen(const String &big, const String &small, bool on) {
  oled.clearDisplay();
  if (on) oled.fillRect(0, 0, W, H, SSD1306_WHITE);
  oled.setTextColor(on ? SSD1306_BLACK : SSD1306_WHITE);
  int y = 24;
  String rest = big;
  while (rest.length()) {
    int sp = rest.indexOf(' ');
    String word = sp < 0 ? rest : rest.substring(0, sp);
    rest = sp < 0 ? "" : rest.substring(sp + 1);
    int size = fitSize(word);
    centred(word, y, size);
    y += size * 8 + 6;
  }
  wrapped(small, y + 10);
  oled.setTextColor(SSD1306_WHITE);
  oled.display();
}

// Called twice a second from the loop.
void screenDraw() {
  if (!oledOk) return;
  static bool blink = false;
  blink = !blink;

  if (factor == 1) { screenMessage("Calibrate", "Not calibrated yet", "Tare with the hook empty", "then hang a known weight"); return; }
  if (isnan(curG)) { screenMessage("IV Monitor", "Reading the scale..."); return; }

  bool alarmOn = alertsOn && valveState != 1;
  if (alarmOn && strcmp(curState, "low") == 0) { alertScreen("LOW", String((int)curMl) + " ml left", blink); return; }
  if (alarmOn && strcmp(curState, "stopped") == 0) { alertScreen("NO FLOW", "valve open, weight steady", blink); return; }

  if (!pageOpened) { screenAddress(); return; }

  oled.clearDisplay();
  statusBar();

  // Amount left: the biggest thing on the screen.
  String ml = String((int)roundf(curMl));
  centred(ml, 16, fitSize(ml));
  centred("ml left", 42, 1);
  oled.drawFastHLine(0, 53, W, SSD1306_WHITE);

  // Time left.
  centred("time left", 57, 1);
  String t = curMins >= 0 ? String(curMins / 60) + ":" + (curMins % 60 < 10 ? "0" : "") + String(curMins % 60) : String("--");
  centred(t, 68, fitSize(t, 2));
  oled.drawFastHLine(0, 85, W, SSD1306_WHITE);

  // Rate, or how long until there is one.
  if (!isnan(curRate)) {
    String r = String((int)roundf(curRate));
    centred(r, 89, fitSize(r, 2));
    centred("ml/h", 105, 1);
  } else {
    int s = n >= MIN_WINDOW_S ? 0 : MIN_WINDOW_S - n;
    char buf[8];
    snprintf(buf, sizeof buf, "%d:%02d", s / 60, s % 60);
    centred("rate in", 91, 1);
    centred(buf, 102, 1);
  }

  valveBand();
  oled.display();
}
