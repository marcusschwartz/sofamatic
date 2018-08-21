#include <Adafruit_SSD1306.h>

#include "logo.h"
#include "spinner.h"

Adafruit_SSD1306 oled = Adafruit_SSD1306();

// width of display in characters
#define DISPLAY_WIDTH 21

byte spinner_position = (128 - spinner_logo_width) / 2;
int spinner_direction = 3;

void setup_display() {
  // start the display
  oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  oled.clearDisplay();
  oled.drawBitmap(0, 0,  sofamatic_logo, sofamatic_logo_width, sofamatic_logo_height, 1);
  oled.setTextSize(1);
  oled.setTextColor(WHITE);
  oled.display();  
}

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

void display_status_large_oneline(String msg) {
  oled.clearDisplay();
  oled.drawBitmap(0, 0,  sofamatic_logo, sofamatic_logo_width, sofamatic_logo_height, 1);
  oled.setTextSize(2);
  display_status_msg(msg, 1, 12, 10, 16);
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

