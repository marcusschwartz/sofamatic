#define INTERRUPT_IGNORE_CYCLES 1
#define INTERRUPT_TRIGGER_TRANSITIONS 8

byte transition_count = 0;
byte non_transition_count = 0;
byte z_was_last_active = 0;

void detect_button_interrupt(void(*interrupt_handler)(void)) {
  char debug[100];

  if (nunchuk.zButton ^ nunchuk.cButton) {
    non_transition_count = 0;
    if ( (nunchuk.zButton && ! z_was_last_active) ||
         (z_was_last_active && ! nunchuk.zButton) ) {
      transition_count += 1;
    }
    z_was_last_active = nunchuk.zButton;
  } else {
    non_transition_count += 1;
    if (non_transition_count > INTERRUPT_IGNORE_CYCLES) {
      transition_count = 0;
      non_transition_count = 0;
      z_was_last_active = 0;
    }
  }

  if (transition_count > INTERRUPT_TRIGGER_TRANSITIONS) {
    interrupt_handler();
    transition_count = 0;
    z_was_last_active = 0;
  }
}
