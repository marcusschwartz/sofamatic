#include <ESP8266WiFi.h>
#include <WiFiUDP.h>

#include "wifi.h"

// after this many milliseconds with no updates from the
// sofa, the spinner is displayed
#define UPDATE_EXPIRATION 3000

// after this many milliseconds with no updates from the
// sofa, the remote goes into lock mode
#define LOCK_MODE_TIMEOUT 20000

// the port that this remote listens on
#define REMOTE_PORT 31338

// where to send data
#define SOFA_ADDR IPAddress(192,168,  3,  1)
#define SOFA_PORT 31337

unsigned long last_update = 0;

WiFiUDP udp;

void setup_network() {
  // start wifi
  WiFi.mode(WIFI_STA); 
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int count = 0;
  while (WiFi.status() != WL_CONNECTED) {
    display_spinner();
    Serial.print(".");
    delay(25);
    if (count++ > 200) {
      enter_lock_mode();
    }
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
    unsigned long update_age = millis() - last_update;
    if (update_age > UPDATE_EXPIRATION) {
      display_spinner();
    }
    if (update_age > LOCK_MODE_TIMEOUT) {
      enter_lock_mode();
    }
    return false;
  }
}

void send_packet(int status_age, unsigned int duty_cycle) {
  char packet[100];
  nunchuk.update();
  if (validate_nunchuk(nunchuk)) {
    sprintf(packet, "%03d:%03d:%1d:%1d:%d:%d:%d", nunchuk.analogX, nunchuk.analogY, 
            nunchuk.zButton, nunchuk.cButton, status_age, duty_cycle, duty_cycle);
    udp.beginPacket(SOFA_ADDR, SOFA_PORT);
    udp.write(packet);
    udp.endPacket();
  }
}
