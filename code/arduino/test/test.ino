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
PubSubClient client(espClient);

void setup() {
	Serial.begin(9600);
	WiFi.begin(ssid, password);
	while (WiFi.status() != WL_CONNECTED) {
		delay(500);
		Serial.println("Connecting to WiFi..");
	}
	Serial.println("Connected to the WiFi network");

	client.setServer(mqttServer, mqttPort);
	client.setCallback(callback);

	while (!client.connected()) {
		Serial.println("Connecting to MQTT...");

		if (client.connect("ESP8266Client", mqttUser, mqttPassword )) {

			Serial.println("connected");  

		} else {

			Serial.print("failed with state ");
			Serial.print(client.state());
			delay(2000);

		}
	}

	client.publish("esp/test", "hello"); //Topic name
	client.subscribe("esp/test");

}

void callback(char* topic, byte* payload, unsigned int length) {
	char message[length+1]; // will later contain only the message, without sender information
	for(int i = 0; i < length; i++){ // copy message from payload to message
		message[i] = (char) payload[i];
	}
	message[length] = '\0'; // add null byte to terminate string
	Serial.println(message);
}

void loop() {
	client.loop();
}
