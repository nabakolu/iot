# Mosquitto server configuration  
### The configuration used to operate our mosquitto server includes:
Port 1884: MQTT&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//used by our sensors and the AI Planner  
Port 4005: Websockets &nbsp;&nbsp;//used to communicate with the web app  
Password protection
### Starting the server
The *run-mosquitto.sh* starts the server using the provided configuration file  
**!!! Before starting, a password file needs to genereated**  
see: https://mosquitto.org/man/mosquitto_passwd-1.html
