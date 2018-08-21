
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
