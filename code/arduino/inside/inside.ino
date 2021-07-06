#include <Servo.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "test"; // Enter your WiFi name
const char* password =  "12345678"; // Enter WiFi password
const char* mqttServer = "82.165.70.137";
const int mqttPort = 1884;
const char* mqttUser = "iotproject";
const char* mqttPassword = "iotaccesspw%";

WiFiClient espClient;
PubSubClient mqtt(espClient);

#define heatinPIN D6
int command = 0;
int power = 0;

bool heating_auto = true;

void set_heating(int x){
	// make some LED stuff
	analogWrite(heatinPIN, map(x, 0, 100, 0, 255));

	char x_s[4];
	itoa(x, x_s, 10);
	mqtt.publish("actuators/heating/status", x_s);
}

void setup() {
	Serial.begin(9600);
	WiFi.begin(ssid, password);
	while (WiFi.status() != WL_CONNECTED) {
		delay(500);
		Serial.println("Connecting to WiFi..");
	}
	Serial.println("Connected to the WiFi network");

	mqtt.setServer(mqttServer, mqttPort);
	mqtt.setCallback(callback);

	while (!mqtt.connected()) {
		Serial.println("Connecting to MQTT...");

		if (mqtt.connect("inside", mqttUser, mqttPassword, "actuators/heating/status", 1, true, "" )) {

			Serial.println("connected");  

		} else {

			Serial.print("failed with state ");
			Serial.print(mqtt.state());
			delay(2000);

		}
	}

	mqtt.subscribe("actuators/heating/command");
	mqtt.subscribe("actuators/heating/power");
	mqtt.subscribe("actuators/heating/mode");

}

void callback(char* topic, byte* payload, unsigned int length) {
	char message[length+1]; // will later contain only the message, without sender information
	for(int i = 0; i < length; i++){ // copy message from payload to message
		message[i] = (char) payload[i];
	}
	message[length] = '\0'; // add null byte to terminate string

	String topic_s = String(topic);
	String message_s = String(message);

	if(topic_s == "actuators/heating/command"){
		command = message_s.toInt();
		if(heating_auto){
			set_heating(command);
		}
	}else if (topic_s == "actuators/heating/power"){
		power = message_s.toInt();
		if(!heating_auto){
			set_heating(power);
		}
	}
	else if(topic_s == "actuators/heating/mode"){
		if(message_s == "auto"){
			heating_auto = true;
			set_heating(command);
		}else if(message_s == "manual"){
			heating_auto = false;
			set_heating(power);
		}
	}


	Serial.print(topic);
	Serial.print(": ");
	Serial.println(message);

}


void loop() {
	mqtt.loop();
}
