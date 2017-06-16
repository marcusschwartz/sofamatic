#!/usr/bin/python

import atexit
import math
import os
import socket
import tempfile
import time
import joystick
import motors

import serial

JOY_MODES = [
    # name, start_angle, m1_speed, m2_speed, accel_profile
    ["STRT", 0, 1.0, 1.0, 'NORMAL'],
    ["TURN", 10, 1.0, 1.0, 'NORMAL'],
    ["TURN", 90, 1.2, 0.8, 'NORMAL'],
    ["CRWL", 135, 1.0, 0.0, 'NORMAL'],
    ["STOP", 165, 0.0, 0.0, 'NORMAL'],
    ["BRAKE", 170, 0.0, 0.0, 'BRAKE'],
    ["", 180, 0.0, 0.0, "BRAKE"],
]

MAX_FWD_SPEED = 0.33
MAX_TURN_FWD_SPEED = 0.33

TURBO_MAX_FWD_SPEED = 1.0
TURBO_MAX_TURN_FWD_SPEED = 0.4

MAX_REV_SPEED = 0.2
MAX_TURN_REV_SPEED = 0.2

MOTOR_MULTIPLIER = 900

PI = 3.14159
E = 2.7182


def shutdown():
    """remove any evidence of our running"""
    try:
        os.unlink("/var/run/sofa_status")
    except:
        pass


def gamma(orig):
    """make smaller values appear larger"""
    output = orig / 10
    gam = (E**(output / 4.1)) - 1
    return gam * 10

def dump_status(mode, submode, magnitude, angle, left_motor, right_motor,
                volts, amps, speed, m1_speed, m2_speed, max_speed):
    """output interesting metrics to stdout and a status file"""
    print("{:8s} {:8s} {:3d}% {:3d}o {:5.0f},{:5.0f} {} {} {:3.2f} {:3.2f} {:3.2f} {:3.2f}".format(
        mode, submode, magnitude, angle, left_motor, right_motor, volts, amps, speed, m1_speed, m2_speed, max_speed))
    status = tempfile.NamedTemporaryFile(dir="/var/run", delete=False)
    status_temp_file = status.name
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    status.write("{}\n".format(now))
    status.write("MODE        {:8s}\n".format(mode))
    status.write("NUNCHUK {:3d}% {:3d}o\n".format(magnitude, angle))
    status.write("MOTOR     {:4.1f} {:4.1f}\n".format(left_motor, right_motor))
    status.write("VOLTS     {}\n".format(volts))
    status.write("AMPS        {}\n".format(amps))
    status.close()
    os.rename(status_temp_file, "/var/run/sofa_status")


def linear_map(i, i_min, i_max, o_min, o_max):
    """mapping function"""
    if o_max > o_min:
        out = (float((i - i_min)) / float(i_max - i_min)) * \
            float(o_max - o_min) + o_min
    else:
        out = (1.0 - (float(i - i_min) / float(i_max - i_min))) * \
            float(o_min - o_max) + o_max
    return out


def process_accel(target_speed, current_speed, accel_profile):
    """do the accel/decel thing"""
    accel_profiles = {
        'NORMAL': [0.05, 0.1, 0.1],
        'TURBO': [0.1, 0.1, 0.1],
        'BRAKE': [0.1, 0.3, 0.1],
    }

    if target_speed > current_speed:
        # accelerate
        accel_rate = accel_profiles[accel_profile][0]
#        print "ACCEL {} {} {}".format(accel_profile, current_speed, accel_rate)
        current_speed += accel_rate
        if current_speed > target_speed:
            current_speed = target_speed

    elif target_speed < current_speed:
        # deccelerate
        decel_rate = accel_profiles[accel_profile][1]
        min_decel_rate = accel_profiles[accel_profile][2]
        if decel_rate < min_decel_rate:
            decel_rate = min_decel_rate
#        print "DECEL {} {} {}".format(accel_profile, current_speed, decel_rate)
        current_speed -= decel_rate
        if current_speed < target_speed:
            current_speed = target_speed

    return current_speed


def cuberoot(n):
    return n ** (1.0 / 3)


class sofa:
    _motor = None
    _nunchuk = None
    
    def __init__(self):
        self._nunchuk = joystick.nunchuk()
	self._motors = motors.roboteq()

    def control_loop(self):
        """the main logic"""
        mode = 'IDLE'
        submode = ''
    
        ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
    
        left_motor = 0.0
        right_motor = 0.0
    
        missed_data = 0
    
        target_speed = 0.0
        current_speed = 0.0
    
        target_m1_speed = 0.0
        target_m2_speed = 0.0
    
        current_m1_speed = 0.0
        current_m2_speed = 0.0
    
        target_max_speed = 0.0
        current_max_speed = 0.0
    
        while True:
            magnitude, angle, button_c, button_z = self._nunchuk.get_joystick()
    
            if magnitude < 0:
                missed_data += 1
                if missed_data > 3:
                    mode = 'OFFLINE'
                    left_motor = 0.0
                    right_motor = 0.0
    
            else:
                missed_data = 0
    
                if mode == 'OFFLINE':
                    mode = 'IDLE'
    
                if mode == 'IDLE':
                    if magnitude > 10:
		        if button_c:
			    if angle <= 45 or angle >= 315:
			        mode = 'SPIN'
		            elif angle > 45 and angle < 135:
			        mode = 'CRAWL'
			    elif angle >= 135 and angle <= 225:
			        mode = 'SPIN'
			    elif angle > 225 and angle < 315:
			        mode = 'CRAWL'
			
                        elif (angle <= 45) or (angle >= 315):
                            mode = 'FORWARD'
                        elif (angle >= 135) and (angle <= 225):
                            mode = 'REVERSE'
    
                elif mode == 'CRAWL':
		    if magnitude < 10 and current_speed == 0:
		        mode = 'IDLE'
			time.sleep(0.1)
			continue

		elif mode == 'SPIN':
		    if magnitude < 10 and current_speed == 0:
		        mode = 'IDLE'
			time.sleep(0.1)
			continue
		     
                elif mode == 'FORWARD' or mode == 'REVERSE':
                    turn_direction = 'NONE'
                    turn_angle = 0
                    submode = ""
                    accel_profile = ""
                    start_angle = 0
                    end_angle = 0
                    start_m1_speed = 0.0
                    end_m1_speed = 0.0
                    start_m2_speed = 0.0
                    end_m2_speed = 0.0
    
                    if magnitude == 0 and current_speed == 0 and target_speed == 0:
                        target_m1_speed = 0.0
                        target_m2_speed = 0.0
                        mode = 'IDLE'
			time.sleep(0.1)
                        continue
    
                    if magnitude > 10 and mode == 'FORWARD':
                        if angle <= 180:
                            turn_direction = 'RIGHT'
                            turn_angle = angle
        #                    print("TURN RIGHT {}".format(turn_angle))
                        else:
                            turn_direction = 'LEFT'
                            turn_angle = 360 - angle
        #                    print("TURN LEFT {}".format(turn_angle))
                    elif magnitude > 10:
                        if angle <= 180:
                            turn_direction = 'RIGHT'
                            turn_angle = 180 - angle
        #                    print("TURN RIGHT {}".format(turn_angle))
                        else:
                            turn_direction = 'LEFT'
                            turn_angle = 180 - (360 - angle)
        #                    print("TURN LEFT {}".format(turn_angle))
    
                    if magnitude > 10:
                        for i in range(0, len(JOY_MODES) - 1):
                            submode, start_angle, start_m1_speed, start_m2_speed, \
                                accel_profile = JOY_MODES[i]
                            next_submode, end_angle, end_m1_speed, end_m2_speed, \
                                next_accel_profile = JOY_MODES[i + 1]
                            if turn_angle >= start_angle and \
                               turn_angle < end_angle:
                                break
    
                        target_m1_speed = linear_map(turn_angle, start_angle,
                                                     end_angle, start_m1_speed,
                                                     end_m1_speed)
                        target_m2_speed = linear_map(turn_angle, start_angle,
                                                     end_angle, start_m2_speed,
                                                     end_m2_speed)
                    else:
                        submode = "COAST"
                        accel_profile = "NORMAL"
    
        #            print("SUBMODE {:6s} {:4.2f} {:4.2f} {} {}".format(
        #                  submode, m1_speed, m2_speed, start_angle, end_angle))
    
                    if mode == 'FORWARD':
                        if button_z:
                            target_max_speed = ((TURBO_MAX_FWD_SPEED -
                                                 TURBO_MAX_TURN_FWD_SPEED) *
                                                ((135.0 - float(turn_angle)) / 135.0)) + \
                                TURBO_MAX_TURN_FWD_SPEED
                        else:
                            target_max_speed = ((MAX_FWD_SPEED - MAX_TURN_FWD_SPEED) *
                                                ((135.0 - float(turn_angle)) / 135.0)) + \
                                MAX_TURN_FWD_SPEED
    
                    elif mode == 'REVERSE':
                        target_max_speed = ((MAX_REV_SPEED - MAX_TURN_REV_SPEED) *
                                            ((135.0 - float(turn_angle)) / 135.0)) + \
                            MAX_TURN_FWD_SPEED
    
                    if submode != 'COAST':
                        target_speed = gamma(magnitude) / 100.0
                    else:
                        target_speed = 0.0
                        target_m1_speed = 0.0
                        target_m2_speed = 0.0
    
                    if accel_profile == 'NORMAL' and button_z:
                        accel_profile = 'TURBO'
    
                    current_speed = process_accel(target_speed, current_speed,
                                                  accel_profile)
                    current_max_speed = process_accel(target_max_speed, current_max_speed,
                                                      accel_profile)
                    current_m1_speed = process_accel(target_m1_speed,
                                                     current_m1_speed,
                                                     accel_profile)
                    current_m2_speed = process_accel(target_m2_speed,
                                                     current_m2_speed,
                                                     accel_profile)
    
    #                print("TARGET {} {} {}".format(target_speed, target_m1_speed,
    #                                               target_m2_speed))
    #                print("CURRENT {} {} {}".format(current_speed, current_m1_speed,
    #                                                current_m2_speed))
    
                    if turn_direction == 'LEFT':
                        left_motor = math.sqrt(
                            current_m2_speed * current_speed) * current_max_speed
                        right_motor = math.sqrt(
                            current_m1_speed * current_speed) * current_max_speed
                    elif turn_direction == 'RIGHT':
                        left_motor = math.sqrt(
                            current_m1_speed * current_speed) * current_max_speed
                        right_motor = math.sqrt(
                            current_m2_speed * current_speed) * current_max_speed
                    else:
                        left_motor = current_speed * current_max_speed
                        right_motor = current_speed * current_max_speed
    
                    left_motor *= 0.96
    
                    if mode == 'REVERSE':
                        left_motor *= -1.0
                        right_motor *= -1.0
    
                    left_motor *= MOTOR_MULTIPLIER
                    right_motor *= MOTOR_MULTIPLIER
    
            self._motors.speed(left_motor, right_motor)
    
            volts = self._motors.volts()
            volts = "{:4.1f} ({:5.2f})".format(volts, volts / 3)

	    amps_l, amps_r = self._motors.amps()
            amps = "{:4.1f} {:4.1f}".format(amps_l, amps_r)
    
            dump_status(mode, submode, magnitude, angle, int(left_motor),
                        int(right_motor), volts, amps, current_speed, current_m1_speed, current_m2_speed, current_max_speed)
            time.sleep(0.1)
    
    
atexit.register(shutdown)
sofamatic = sofa()
sofamatic.control_loop()
