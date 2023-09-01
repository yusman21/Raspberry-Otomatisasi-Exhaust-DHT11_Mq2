from ubidots import ApiClient
import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
relay_pin = 13
relay_pin2 = 19
mq2_pin = 17
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.setup(relay_pin2, GPIO.OUT)
GPIO.setup(mq2_pin, GPIO.IN)

# Set relay initial state to HIGH
GPIO.output(relay_pin, GPIO.HIGH)
GPIO.output(relay_pin2, GPIO.HIGH)

api = ApiClient(token='BBFF-Fsqb5LjmOk3hVIccc0NHAnGsaw03wF')

try:
    fan_variable = api.get_variable("64d9b12c2571031f8cca7b27")
    humidity_variable = api.get_variable("64d9aae825517617ff07120a")
    temperature_variable = api.get_variable("64d9aad003c3043b4e90fa8d")
    mq2_variable = api.get_variable("64d99865257103d15e7f6fff")
    button_variable = api.get_variable("64d9b414ba378f000bd79ce3")
    lamp_variable = api.get_variable("64d9b3503400e379c10879b2")
except ValueError:
    print("It is not possible to obtain the variable")

dht_sensor = Adafruit_DHT.DHT11
dht_pin = 4

lamp_status = 1

RST = None
DC = 23

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)
disp.begin()

disp.clear()
disp.display()

title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
text_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 10)
value_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)

while True:
    try:
        humidity, temperature = Adafruit_DHT.read_retry(dht_sensor, dht_pin)
        
        if humidity is not None and temperature is not None:
            humidity_variable.save_value({'value': humidity})
            temperature_variable.save_value({'value': temperature})

            print(f"Suhu: {temperature:.1f}°C, Kelembapan: {humidity:.1f}%")

            mq2_value = GPIO.input(mq2_pin)

            mq2_variable.save_value({'value': mq2_value})

            if mq2_value == 0 or temperature > 32:
                GPIO.output(relay_pin, GPIO.LOW)
                print("Relay ON")
                fan_variable.save_value({"value": 1})
                time.sleep(10)
            else:
                GPIO.output(relay_pin, GPIO.HIGH)
                print("Relay OFF")
                fan_variable.save_value({"value": 0})

            last_button_value = button_variable.get_values(1)
            button_status = last_button_value[0].get("value")

            if button_status == 0:
                lamp_status = 0
            else:
                lamp_status = 1
        
            lamp_variable.save_value({"value": lamp_status})
            GPIO.output(relay_pin2, GPIO.LOW if lamp_status == 1 else GPIO.HIGH)
            print(f"Lampu {'ON' if lamp_status == 1 else 'OFF'}")

            width = disp.width
            height = disp.height
            image = Image.new('1', (width, height))
            draw = ImageDraw.Draw(image)

            air_status_text = "Udara Aman" if mq2_value == 1 else "ADA GAS..!!!"
            draw.text((5, 0), air_status_text, font=title_font, fill=255)

            draw.text((5, 15), "Suhu:", font=text_font, fill=255)
            draw.text((5, 25), f"{temperature:.1f} °C", font=value_font, fill=255)
            draw.text((5, 40), "Kelembapan:", font=text_font, fill=255)
            draw.text((5, 50), f"{humidity:.1f} %", font=value_font, fill=255)

            disp.image(image)
            disp.display()

        else:
            print("Error reading DHT11 sensor")

        time.sleep(1)
    except Exception as e:
        print("An error occurred:", str(e))
