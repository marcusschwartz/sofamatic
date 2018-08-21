#define DEEP_SLEEP_INTERVAL 5000000

bool check_lock_mode() {
  unsigned int lock_mode;
  
  ESP.rtcUserMemoryRead(0, &lock_mode, sizeof(lock_mode));
  if (lock_mode == 31337) {
    return true;
  }
  return false;
}

void set_lock_mode(bool lock_mode) {
  unsigned int rtc_lock_mode = 0;
  if (lock_mode) {
    rtc_lock_mode = 31337;
  }
  ESP.rtcUserMemoryWrite(0, &rtc_lock_mode, sizeof(lock_mode));
}
    
void enter_lock_mode() {
  oled.clearDisplay();
  oled.display();
  delay(50);
  set_lock_mode(true);
  ESP.deepSleep(DEEP_SLEEP_INTERVAL);
}

void exit_lock_mode() {
  set_lock_mode(false);
  ESP.restart();
}

void wait_for_unlock() {
  Serial.begin(115200);
  Serial.println("Starting up locked...");
  setup_display();
  display_status_large_oneline("LOCKED");
  for (int i = 0; i <= 100; i++) {
    nunchuk.update();
    detect_button_interrupt(&exit_lock_mode);
    delay(PACKET_INTERVAL);
  }
  enter_lock_mode();
}

void handle_lock_mode() {
  if (check_lock_mode()) {
    setup_nunchuk();
    nunchuk.update();
    if (nunchuk.zButton || nunchuk.cButton) {
      wait_for_unlock();
    } else {
      ESP.deepSleep(DEEP_SLEEP_INTERVAL);
    }  
  }
}
