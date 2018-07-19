#include <ArduinoJson.h>

#include <ESP8266HTTPClient.h>

#include <Wire.h>
#include <ArduinoNunchuk.h>
#include <ESP8266WiFi.h>
#include <WiFiUDP.h>
#include <time.h>
#include <Adafruit_SSD1306.h>

#include "logo.h"
#include "spinner.h"

#ifdef ESP8266
   #define STMPE_CS 16
   #define TFT_CS   0
   #define TFT_DC   15
   #define SD_CS    2
#endif

// width of display in characters
#define DISPLAY_WIDTH 21

// milliseconds between packet sends
#define PACKET_INTERVAL 100 

// max milliseconds between updates from sofa
#define UPDATE_EXPIRATION 3000

#define REMOTE_PORT 31338
#define SOFAMATIC_GRP IPAddress(224, 0, 0, 250)
#define SOFA_ADDR IPAddress(192,168,  3,  1)
#define SOFA_PORT 31337

Adafruit_SSD1306 oled = Adafruit_SSD1306();
ArduinoNunchuk nunchuk = ArduinoNunchuk();
WiFiUDP udp;

unsigned long last_millis = millis();
unsigned long last_update = 0;

unsigned long last_status_update = 0;

byte spinner_position = (128 - spinner_logo_width) / 2;
int spinner_direction = 3;

void display_status_msg(String msg, int row, byte char_width, byte screen_chars, byte char_height) {
  int padding = (char_width * (screen_chars - msg.length())) / 2;
  oled.setCursor(padding,row * char_height);
  oled.print(msg);
}

void display_status(String msg1, String msg2) {
  oled.clearDisplay();
  oled.drawBitmap(0, 0,  sofamatic_logo, sofamatic_logo_width, sofamatic_logo_height, 1);
  oled.setTextSize(1);
  display_status_msg(msg2, 2, 6, 21, 8);
  display_status_msg(msg1, 3, 6, 21, 8);
  oled.display();
}

void display_status_large(String msg1, String msg2) {
  oled.fillRect(0, 0, 128, 32, BLACK);
  oled.setTextSize(2);
  display_status_msg(msg2, 1, 12, 10, 16);
  display_status_msg(msg1, 0, 12, 10, 16);
  oled.display();
}

void display_spinner() {
   byte spinner_left_boundary = 24;
   byte spinner_right_boundary = 128 - spinner_left_boundary - spinner_logo_width;
   byte spinner_step = 3;
   
   oled.clearDisplay();
   oled.drawBitmap(0, 0,  sofamatic_logo, sofamatic_logo_width, sofamatic_logo_height, 1);
   if (spinner_direction > 0) {
     oled.drawBitmap(spinner_position, 16, spinner_logo_right, spinner_logo_width, spinner_logo_height, 1);
   } else {
     oled.drawBitmap(spinner_position, 16, spinner_logo_left, spinner_logo_width, spinner_logo_height, 1);
   }
   oled.display();
   if (spinner_position >= spinner_right_boundary) {
     spinner_position = spinner_right_boundary;
     spinner_direction = -1 * spinner_step;
   }
   if (spinner_position <= spinner_left_boundary) {
     spinner_position = spinner_left_boundary;
     spinner_direction = spinner_step;
   }
   spinner_position += spinner_direction;
}

void setup_oled() {
  // start the display
  oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  oled.clearDisplay();
  oled.drawBitmap(0, 0,  sofamatic_logo, sofamatic_logo_width, sofamatic_logo_height, 1);
  oled.setTextSize(1);
  oled.setTextColor(WHITE);
  oled.display();  
}

void setup_nunchuk() {
  // set up nunchuk pins
  pinMode(15, OUTPUT);
  digitalWrite(15, HIGH);
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  pinMode(0, OUTPUT);

  // start the nunchuk
  delay(50);
  nunchuk.init();  
}

void setup_wifi() {
  // start wifi
  WiFi.mode(WIFI_STA); 
  WiFi.begin("SofaMatic", "GoingPlaces");
  //WiFi.begin("Poison Tree Frog", "DeltaZoonii");
  //WiFi.begin("AndroidAP 420", "catalyst");
  while (WiFi.status() != WL_CONNECTED) {
    display_spinner();
    Serial.print(".");
    delay(25);
  }
  display_status(WiFi.localIP().toString(), "");
  //udp.beginMulticast(WiFi.localIP(), SOFAMATIC_GRP, REMOTE_PORT);
  udp.begin(REMOTE_PORT);
}

bool process_status_packet() {
  char packet_buffer[2 * DISPLAY_WIDTH + 1];
  int packet_size = udp.parsePacket();
  int len = udp.read(packet_buffer, 2 * DISPLAY_WIDTH + 1);
  if (len > 0) {
    char msg1[DISPLAY_WIDTH + 1];
    char msg2[DISPLAY_WIDTH + 1];
    last_update = millis();
    packet_buffer[len] = 0;

    bool large = false;
    byte offset = 0;
    if (packet_buffer[0] == '&') {
      offset = 1;
      large = true;
    }
    // split the packet into two rows on ~
    char *sep = strchr(packet_buffer + offset, '~');
    if (sep) {
      strncpy(msg1, packet_buffer + offset, DISPLAY_WIDTH);
      msg1[strlen(packet_buffer + offset) - strlen(sep)] = 0;
      strncpy(msg2, sep + 1, DISPLAY_WIDTH);
      msg2[DISPLAY_WIDTH] = 0;
    } else {
      strncpy(msg1, packet_buffer + offset, DISPLAY_WIDTH);
      msg1[DISPLAY_WIDTH] = 0;
      strncpy(msg2, "", DISPLAY_WIDTH);
      msg2[DISPLAY_WIDTH] = 0;
    }

    if (large) { 
      display_status_large(msg1, msg2);
    } else {
      display_status(msg1, msg2);
    }
    return true;
  } else {
    if ((millis() - last_update) > UPDATE_EXPIRATION) {
      display_spinner();
    }
    return false;
  }
  
}

bool validate_nunchuk(ArduinoNunchuk nunchuk) {
  if (
      ((nunchuk.analogX < 0) || (nunchuk.analogX > 255)) ||
      ((nunchuk.analogY < 0) || (nunchuk.analogY > 255)) ||
      ((nunchuk.zButton < 0)  || (nunchuk.zButton > 1)) ||
      ((nunchuk.cButton < 0)  || (nunchuk.cButton > 1)) ||
      ((nunchuk.analogX == 255) && (nunchuk.analogY == 255))
     ) {
    display_status("JOYSTICK ERROR", "");
    Serial.println("BAD JOYSTICK DATA ");
    nunchuk.init();
    delay(50);
    return false;
  }
  return true;
}

void send_packet(int status_age) {
  char packet[100];
  nunchuk.update();
  if (validate_nunchuk(nunchuk)) {
    sprintf(packet, "%03d:%03d:%1d:%1d:%d", nunchuk.analogX, nunchuk.analogY, nunchuk.zButton,nunchuk.cButton, status_age);
    //udp.beginPacketMulticast(SOFAMATIC_GRP, SOFA_PORT, WiFi.localIP(), 1);
    udp.beginPacket(SOFA_ADDR, SOFA_PORT);
    udp.write(packet);
    udp.endPacket();
  }
}

void sleep_a_while() {
  unsigned long now = millis();
  unsigned long loop_delay = now - last_millis;
  Serial.print("loop delay ");
  Serial.println(loop_delay);
  if (loop_delay < PACKET_INTERVAL) {
    delay(PACKET_INTERVAL - loop_delay);
  }
  last_millis = millis();
}

void setup() {
  // turn off the LED
  pinMode(BUILTIN_LED, OUTPUT);
  digitalWrite(BUILTIN_LED, HIGH);

  Serial.begin(115200);
  Serial.println("Starting up...");

  setup_oled();
  setup_nunchuk();
  setup_wifi();
}

void loop() {
  // handle any status updates if available
  unsigned long now = millis();
  int status_age = -1;
  
  if (process_status_packet()) {
    last_status_update = now;
  }

  // sleep for a bit if necessary
  sleep_a_while();

  // send another data packet
  if (last_status_update > 0) {
    status_age = now - last_status_update;
  }
  send_packet(status_age);
}
