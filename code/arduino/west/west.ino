/* Arduino sketch for nodemcuv2
 * location: west
 * actuators: windows, blinds
 * sensors: light
*/

#include <Servo.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define window_pin D1
#define blinds_pin D8
#define light_pin A0


const char* ssid = "test"; // WiFi name
const char* password =  "12345678"; // WiFi password
const char* mqttServer = "82.165.70.137"; // mqtt broker ip
const int mqttPort = 1884; // mqtt broker port
const char* mqttUser = "iotproject"; // mqtt user
const char* mqttPassword = "iotaccesspw%"; // mqtt password

Servo window; // Servo for window
Servo blinds; // Servo for blinds

bool window_auto = true; //specifies, if messages send from AI planning are to be followed (true), or if manual open/close is activated (false);
bool blinds_auto = true; //specifies, if messages send from AI planning are to be followed (true), or if manual open/close is activated (false);

WiFiClient espClient; // WiFiClient to connect and use WiFi
PubSubClient mqtt(espClient); // mqtt client

// closes the window and sens appropriate retained status message to mqtt broker
void close_window(){
	window.write(0);
	mqtt.publish("actuators/windows/west/status", "closed", true);
}


// opens the window and sens appropriate retained status message to mqtt broker
void open_window(){
	window.write(180);
	mqtt.publish("actuators/windows/west/status", "open", true);
}


// closes the blinds and sens appropriate retained status message to mqtt broker
void close_blinds(){
	blinds.write(0);
	mqtt.publish("actuators/blinds/west/status", "closed", true);
}


// opens the blinds and sens appropriate retained status message to mqtt broker
void open_blinds(){
	blinds.write(180);
	mqtt.publish("actuators/blinds/west/status", "open", true);
}




void setup() {
	Serial.begin(9600);
	// Connect to WiFi
	WiFi.begin(ssid, password);
	while (WiFi.status() != WL_CONNECTED) {
		delay(500);
		Serial.println("Connecting to WiFi..");
	}
	Serial.println("Connected to the WiFi network");

	// Set mqtt config
	mqtt.setServer(mqttServer, mqttPort);
	mqtt.setCallback(callback);

	// Connect to mqtt broker
	while (!mqtt.connected()) {
		Serial.println("Connecting to MQTT...");

		if (mqtt.connect("west", mqttUser, mqttPassword, "actuators/windows/west/status", 1, true, "" )) {

			Serial.println("connected");

		} else {

			Serial.print("failed with state ");
			Serial.print(mqtt.state());
			delay(2000);

		}
	}

	// subscribe to topics
	mqtt.subscribe("actuators/windows/west/command");
	mqtt.subscribe("actuators/windows/west/mode");
	mqtt.subscribe("actuators/blinds/west/command");
	mqtt.subscribe("actuators/blinds/west/mode");



	// attach servos to pins
	window.attach(window_pin);
	blinds.attach(blinds_pin);

	// starting position is window and blind closed
	close_window();
	close_blinds();
}

// callback function gets called for each incoming message
void callback(char* topic, byte* payload, unsigned int length) {
	char message[length+1]; // will later contain only the message, without sender information
	for(int i = 0; i < length; i++){ // copy message from payload to message
		message[i] = (char) payload[i];
	}
	message[length] = '\0'; // add null byte to terminate string

	String topic_s = String(topic);
	String message_s = String(message);

	if(topic_s == "actuators/windows/west/mode"){
		if(message_s == "open"){
			open_window();
			window_auto = false;
		}else if(message_s == "close"){
			close_window();
			window_auto = false;
		}else if(message_s == "auto"){
			window_auto = true;
		}
	}else if(topic_s == "actuators/windows/west/command" && window_auto){
		if(message_s == "open"){
			open_window();
		}else if(message_s == "close"){
			close_window();
		}
	}else if (topic_s == "actuators/blinds/west/mode"){
		if(message_s == "open"){
			open_blinds();
			blinds_auto = false;
		}else if(message_s == "close"){
			close_blinds();
			blinds_auto = false;
		}else if(message_s == "auto"){
			blinds_auto = true;
		}
	}else if (topic_s == "actuators/blinds/west/command" && blinds_auto){
		if(message_s == "open"){
			open_blinds();
		}else if(message_s == "close"){
			close_blinds();
		}
	}


	Serial.print(topic);
	Serial.print(": ");
	Serial.println(message);

}

void loop() {
	mqtt.loop();
	delay(1000);
	char msg[8];
	itoa(analogRead(light_pin), msg, 10);
	mqtt.publish("sensors/sun/west", msg, true);
}
