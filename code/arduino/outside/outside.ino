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

#define rainPIN D4

void setup() {
	Serial.begin(9600);
	// connect to WiFi
	WiFi.begin(ssid, password);
	while (WiFi.status() != WL_CONNECTED) {
		delay(500);
		Serial.println("Connecting to WiFi..");
	}
	Serial.println("Connected to the WiFi network");

	// set mqtt config
	mqtt.setServer(mqttServer, mqttPort);

	// connect to mqtt broker
	while (!mqtt.connected()) {
		Serial.println("Connecting to MQTT...");

		if (mqtt.connect("outside", mqttUser, mqttPassword, "sensors/rain", 1, true, "" )) {

			Serial.println("connected");  

		} else {

			Serial.print("failed with state ");
			Serial.print(mqtt.state());
			delay(2000);

		}
	}

}


void loop() {
	int val = 1 - digitalRead(rainPIN); // read sensor data
	char val_s[2];
	itoa(val, val_s, 10); // convert data to string
	mqtt.publish("sensors/rain", val_s); // publish data
	delay(1000);
}
