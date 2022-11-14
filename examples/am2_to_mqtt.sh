# Alberto - Nov 2022

# bank of 4 batteries connected to /dev/ttyUSB1

python3 am2_to_mqtt.py --device=/dev/ttyUSB1 --max-address 4 \
                       --mqtt --mqtt-broker localhost \
                       --mqtt-user 'your-user' --mqtt-password 'your-password' \
                       --mqtt-hass --mqtt-hass-retain
