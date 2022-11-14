# Alberto - Nov 2022

# clear mqtt retained messages with

USER=${1:?USER}
PASS=${2:?PASS}

TAG="am2_battery"

mosquitto_sub -h localhost -v -d -u "$USER" -P "$PASS" --retained-only -t "#" | 
awk "\$1 ~ /${TAG}/ { print }" |
while read TOPIC REST
do
   # mosquitt_pub -r (retain) -n (null) message clear retained message
   echo "Clear $TOPIC"
   mosquitto_pub -h localhost -u "$USER" -P "$PASS" -t '$TOPIC' -r -n
done
