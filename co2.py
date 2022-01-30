#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
Blah
"""
import subprocess
import time
import json
import mh_z19
import RPi.GPIO as GPIO
import os
from pathlib import Path
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106, ssd1306
from PIL import ImageFont, ImageDraw, Image, ImageOps


GPIO.setmode(GPIO.BCM)
RED = 18
YELLOW = 1
GREEN = 24
CO2_CRITICAL = 1000
CO2_WARNING = 700
CO2_LOW = 430
GPIO.setup(RED, GPIO.OUT, initial=False)
GPIO.setup(YELLOW, GPIO.OUT, initial=False)
GPIO.setup(GREEN, GPIO.OUT, initial=False)
SERIAL = i2c(port=1, address=0x3C)
DEVICE = sh1106(SERIAL)
FONT = ImageFont.truetype('coolvetica rg.otf', 26)
IMG_PATH = str(Path(__file__).resolve().parent.joinpath('ventilator_48x48.png'))

subprocess.run("echo none > /sys/class/leds/led0/trigger", shell=True)
subprocess.run("echo none > /sys/class/leds/led1/trigger", shell=True)
os.system("sudo sh -c 'echo 0 > /sys/class/leds/led0/brightness'") # red

def invert_image(img):
    if image.mode == 'RGBA':
        r,g,b,a = image.split()
        rgb_image = Image.merge('RGB', (r,g,b))
        inverted_image = ImageOps.invert(rgb_image)
        r2,g2,b2 = inverted_image.split()
        final_inverted_image = Image.merge('RGBA', (r2,g2,b2,a))
    else:
        final_inverted_image = ImageOps.invert(image)
    return final_inverted_image

def rotate_vent():
    for angle in range(10):
        rotated = BACKGROUND.rotate(angle*10)
        DEVICE.display(rotated.convert(DEVICE.mode))

def set_green():
    subprocess.run("sudo sh -c 'echo 1 > /sys/class/leds/led0/brightness'", shell=True) #green on
    subprocess.run("sudo sh -c 'echo 0 > /sys/class/leds/led1/brightness'", shell=True) #red off
    GPIO.output(GREEN, True)
    GPIO.output(YELLOW, False)
    GPIO.output(RED, False)

def set_yellow():
    subprocess.run("sudo sh -c 'echo 1 > /sys/class/leds/led0/brightness'", shell=True) #green on
    subprocess.run("sudo sh -c 'echo 1 > /sys/class/leds/led1/brightness'", shell=True) #red on
    GPIO.output(GREEN, False)
    GPIO.output(YELLOW, True)
    GPIO.output(RED, False)

def set_red():
    subprocess.run("sudo sh -c 'echo 0 > /sys/class/leds/led0/brightness'", shell=True) #green off
    subprocess.run("sudo sh -c 'echo 1 > /sys/class/leds/led1/brightness'", shell=True) #red on
    GPIO.output(GREEN, False)
    GPIO.output(YELLOW, False)
    GPIO.output(RED, True)
    time.sleep(2)
    rotate_vent()

def set_none():
    subprocess.run("sudo sh -c 'echo 0 > /sys/class/leds/led0/brightness'", shell=True) #green off
    subprocess.run("sudo sh -c 'echo 0 > /sys/class/leds/led1/brightness'", shell=True) #red off
    GPIO.output(GREEN, False)
    GPIO.output(YELLOW, False)
    GPIO.output(RED, False)

try:
    image = Image.open(IMG_PATH)
    LOGO = invert_image(image)
    EMPTY_BACKGROUND = Image.new("RGBA", DEVICE.size, "black")
    POSN = ((DEVICE.width - image.width) // 2, (DEVICE.height - image.height) // 2)
    FFF = Image.new(LOGO.mode, LOGO.size, (0,) * 4)
    IMG = Image.composite(LOGO, FFF, LOGO)
    BACKGROUND = EMPTY_BACKGROUND
    BACKGROUND.paste(IMG, POSN)

    while True:
        X = mh_z19.read()
        VALUE = X["co2"]
        print(VALUE)
        with canvas(DEVICE) as draw:
            draw.text((0, 0), "CO₂", font=FONT, fill="white")
            draw.text((70, 0), str(VALUE), font=FONT, fill="white")
            #draw.text((0, 30), "Tmp", font=FONT, fill="white")
            #draw.text((70, 30), "99", font=FONT, fill="white")
            #draw.text((100, 30), "°C", font=FONT, fill="white")

        if VALUE > CO2_CRITICAL:
            set_red()
        elif VALUE > CO2_WARNING:
            set_yellow()
        elif VALUE < CO2_LOW:
            set_green()
            time.sleep(1)
            set_none()
        else:
            set_green()
        time.sleep(1)
except Exception as error:
    print("Error '{0}' occured. Arguments {1}.".format(error.message, error.args))
    subprocess.run("echo mmc0 > /sys/class/leds/led0/trigger", shell=True)
    subprocess.run("echo input > /sys/class/leds/led1/trigger", shell=True)
    GPIO.cleanup()
except KeyboardInterrupt:
    GPIO.cleanup()
    subprocess.run("echo mmc0 > /sys/class/leds/led0/trigger", shell=True)
    subprocess.run("echo input > /sys/class/leds/led1/trigger", shell=True)