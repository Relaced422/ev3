#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, UltrasonicSensor, GyroSensor, ColorSensor
from pybricks.parameters import Port, Button
from pybricks.tools import wait
from pybricks.robotics import DriveBase
from random import shuffle

# Create your objects here.
ev3 = EV3Brick()

left_motor  = Motor(Port.B)
right_motor = Motor(Port.C)
sonar       = UltrasonicSensor(Port.S4)
gyro        = GyroSensor(Port.S2)
line_sensor = ColorSensor(Port.S3)

robot = DriveBase(left_motor, right_motor, wheel_diameter=55.5, axle_track=104)

# ── Changeable variables ──────────────────────────────────────────────
SCAN_STEP        = 5
DRIVE_SPEED      = 10
PUSH_EXTRA       = 80
OBJECT_THRESHOLD = 300
OBJECT_CENTER_OFFSET = 8
STOP_BEFORE      = 0
TURN_SPEED       = 150
TURN_MIN_SPEED   = 20
TURN_GAIN        = 3.0
BLACK            = 9
WHITE            = 85
LINE_SPEED       = 70
LINE_GAIN        = 1.2
# ─────────────────────────────────────────────────────────────────────

def gyro_turn(target_angle):
    while True:
        error = target_angle - gyro.angle()
        if abs(error) <= 1:
            robot.stop()
            break
        speed = error * TURN_GAIN
        if speed > 0:
            speed = max(TURN_MIN_SPEED, min(speed, TURN_SPEED))
        else:
            speed = min(-TURN_MIN_SPEED, max(speed, -TURN_SPEED))
        robot.drive(0, speed)
        wait(10)
    robot.stop()
    wait(50)

def scan_objects():
    ev3.speaker.say("Scanning for objects")
    gyro.reset_angle(0)
    wait(500)

    raw = []
    for step in range(0, 360, SCAN_STEP):
        gyro_turn(step)
        wait(80)
        dist = sonar.distance()
        if dist < OBJECT_THRESHOLD:
            ev3.speaker.beep()
            raw.append((step, dist))

    objects = []
    group_start_angle = None
    for angle, dist in raw:
        if group_start_angle is None or angle - group_start_angle > SCAN_STEP * 4:
            objects.append((angle, dist))
            group_start_angle = angle
        elif dist < objects[-1][1]:
            objects[-1] = (objects[-1][0], dist)

    ev3.speaker.say(str(len(objects)) + " objects found")
    gyro_turn(0)
    wait(300)
    return objects

def remove_object(angle, distance):
    gyro_turn(angle + OBJECT_CENTER_OFFSET)
    wait(200)
    drive_dist = distance - STOP_BEFORE + PUSH_EXTRA
    robot.straight(drive_dist)
    wait(200)
    robot.straight(-drive_dist)
    wait(200)
    

# ── Mode 1: Remove on detect ──────────────────────────────────────────
# Spins around and pushes away each object the moment it sees one.
# Works
def mode_remove_on_detect():
    ev3.speaker.say("Remove on detect")
    gyro.reset_angle(0)
    wait(500)
    last_object_angle = -999
    for step in range(0, 360, SCAN_STEP):
        gyro_turn(step)
        wait(80)
        dist = sonar.distance()
        if dist < OBJECT_THRESHOLD and step - last_object_angle > SCAN_STEP * 4:
            ev3.speaker.beep()
            ev3.speaker.say("Object found. Removing.")
            last_object_angle = step
            remove_object(step, dist)
            
    ev3.speaker.say("All objects removed")

# ── Mode 2: Scan then remove in order ────────────────────────────────
# Scans the full 360 first, then removes objects one by one
# starting from the first one found going clockwise.
# Doesnt work
def mode_scan_then_remove_in_order():
    ev3.speaker.say("Scan, then remove in order")
    objects = scan_objects()

    for i, (angle, dist) in enumerate(objects):
        ev3.speaker.say("Removing object " + str(i + 1))
        remove_object(angle, dist)

    ev3.speaker.say("All objects removed")

# ── Mode 3: Scan then remove randomly ────────────────────────────────
# Scans the full 360 first, then removes objects in a random order.
# Doesnt work
def mode_scan_then_remove_randomly():
    ev3.speaker.say("Scan, then remove randomly")
    objects = scan_objects()
    shuffle(objects)
    for i, (angle, dist) in enumerate(objects):
        ev3.speaker.say("Removing object " + str(i + 1))
        remove_object(angle, dist)
        gyro_turn(0)
    ev3.speaker.say("All objects removed")

# ── Mode 4: Scan then remove furthest first ───────────────────────────
# Scans the full 360 first, then removes the furthest object first
# and works its way inward to the closest.
# Doesnt work
def mode_scan_then_remove_furthest_first():
    ev3.speaker.say("Scan, then remove furthest first")
    objects = scan_objects()
    objects.sort(key=lambda x: -x[1])
    for i, (angle, dist) in enumerate(objects):
        ev3.speaker.say("Removing object " + str(i + 1))
        remove_object(angle, dist)
    ev3.speaker.say("All objects removed")

# ── Mode 5: Follow a line ─────────────────────────────────────────────
# Uses the color sensor to follow a black line on the floor.
# Press CENTER to stop.
# Works
def mode_follow_line():
    ev3.speaker.say("Following line. Press center to stop.")
    threshold = (BLACK + WHITE) / 2
    while Button.CENTER not in ev3.buttons.pressed():
        deviation = line_sensor.reflection() - threshold
        robot.drive(LINE_SPEED, LINE_GAIN * deviation)
        wait(10)
    robot.stop()
    ev3.speaker.say("Stopped")

# ── Menu ──────────────────────────────────────────────────────────────
MODES = [
    ("Remove on detect",          mode_remove_on_detect),
    ("Scan, remove in order",     mode_scan_then_remove_in_order),
    ("Scan, remove randomly",     mode_scan_then_remove_randomly),
    ("Scan, furthest first",      mode_scan_then_remove_furthest_first),
    ("Follow line",               mode_follow_line),
]

selected = 0
ev3.speaker.say("Select a mode")

while True:
    ev3.screen.clear()
    ev3.screen.print(MODES[selected][0])
    ev3.screen.print("UP/DOWN: change")
    ev3.screen.print("CENTER: start")

    while True:
        pressed = ev3.buttons.pressed()
        if Button.UP in pressed:
            selected = (selected - 1) % len(MODES)
            wait(400)
            break
        elif Button.DOWN in pressed:
            selected = (selected + 1) % len(MODES)
            wait(400)
            break
        elif Button.CENTER in pressed:
            wait(300)
            ev3.speaker.say(MODES[selected][0])
            wait(300)
            MODES[selected][1]()
            ev3.speaker.say("Select a mode")
            break
        wait(50)