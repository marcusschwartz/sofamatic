#include <ArduinoNunchuk.h>
#include <time.h>

// milliseconds between packet sends
#define PACKET_INTERVAL 100 

unsigned long last_millis = millis();

unsigned long last_status_update = 0;

ArduinoNunchuk nunchuk = ArduinoNunchuk();

unsigned int sleep_a_while() {
  unsigned long now = millis();
  unsigned long loop_delay = now - last_millis;
  //Serial.print("loop delay ");
  //Serial.println(loop_delay);
  if (loop_delay < PACKET_INTERVAL) {
    delay(PACKET_INTERVAL - loop_delay);
  }
  unsigned int duty_cycle = (100 * loop_delay) / PACKET_INTERVAL;
  last_millis = millis();
  return(duty_cycle);
}

void setup() {
  // turn off the LED
  pinMode(BUILTIN_LED, OUTPUT);
  digitalWrite(BUILTIN_LED, HIGH);
  
  handle_lock_mode();
  
  Serial.begin(115200);
  Serial.println("Starting up...");

  setup_display();
  setup_nunchuk();
  setup_network();
}

void loop() {
  // handle any status updates if available
  unsigned long now = millis();
  int status_age = -1;
  
  if (process_status_packet()) {
    last_status_update = now;
  }

  // sleep for a bit if necessary
  unsigned int duty_cycle = sleep_a_while();

  // send another data packet
  if (last_status_update > 0) {
    status_age = now - last_status_update;
  }
  send_packet(status_age, duty_cycle);

  // check for a button interrupt
  detect_button_interrupt(&enter_lock_mode);
}
