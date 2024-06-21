import time
from datetime import datetime
import picar_4wd as fc
from picamera2 import Picamera2
from libcamera import controls
from evdev import InputDevice, categorize, ecodes

ORIGIN = 32768
DEBOUNCE = 0.0

dead_zone = 100 # edit me
DEAD_ZONE = min(dead_zone, 32768)

def record_photo(cam):
    '''
    Callback to take a photo. Should run asynchronously in case the camera isn't connected.
    If the camera gets disconnected miduse it may take a while for the driver to realize it.
    '''
    now = datetime.now()
    fn = "photos/" + now.strftime("%Y%m%d-%H%M") + ".jpg"
    cam.capture_file(fn)

def power_control(joystick):
    '''
    linear control
    power = int(abs(joystick) * (100/ORIGIN))
    '''
    scale = 1 # edit me
    power = min(100,scale * int(joystick**2 * 100/ORIGIN**2))
    return power

if __name__ == '__main__':
    print("If you want to quit. Please press start")

    cam = Picamera2()
    cam.stop()
    cam_config = cam.create_still_configuration(main={"size": (2304, 1296)})
    cam.configure(cam_config)
    cam.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})
    cam.start()

    gamepad = InputDevice('/dev/input/event2')
    for event in gamepad.read_loop():
        if event.type == ecodes.EV_ABS:
            t    = event.timestamp()
            type = event.type
            val  = event.value
            power = power_control(val-ORIGIN)
            if event.code == 1:
                if val < ORIGIN - DEAD_ZONE:
                    fc.forward(power)
                if val > ORIGIN + DEAD_ZONE:
                    fc.backward(power)
                if val >= ORIGIN - DEAD_ZONE and val <= ORIGIN + DEAD_ZONE:
                    fc.stop()
            if event.code == 3:
                if val < ORIGIN - DEAD_ZONE:
                     fc.turn_left(power)
                if val > ORIGIN + DEAD_ZONE:
                    fc.turn_right(power)
                if val >= ORIGIN - DEAD_ZONE and val <= ORIGIN + DEAD_ZONE:
                    fc.stop()
        time.sleep(DEBOUNCE)

        if event.type == ecodes.EV_KEY:
            if event.code == 310:
                record_photo(cam)
            if event.code == 311:
                print("quit")
                break

    cam.stop()
