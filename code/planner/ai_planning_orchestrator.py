#%%
from typing import List, Union
import paho.mqtt.client as mqtt
import uuid
import json
from threading import Thread, Lock
from dataclasses import dataclass, field

#thresholds for maximum change that can occur to a value before recalculation is triggered
CHANGE_THRESHOLDS = {"temperature": 1, "noise": 2, "wind": 1.5, "sun": 0.5, "rain": 0.5}

@dataclass
class ActuatorState:
    """stores information about one actuator (window|blind)
    """
    #current operating mode (auto|manual)
    operation_mode: str
    #state the actuator is currently in (open|closed)
    current_state: Union[str,float]

@dataclass
class Preferences:
    """stores user preferences for ambient influences
    """
    #preferences for different measurements
    co2: str = None
    light: str = None
    noise: str = None
    wind: str = None
    #list of lenght 2 with [min, max]
    temperature: List = field(default_factory=lambda: [None, None]) 

    def __repr__(self) -> str:
        r_str = ""
        for i in ["co2", "light", "noise", "wind", "temperature"]:
            r_str += f"Pref for {i} is: {self.__dict__[i]}\n"
        return r_str

#used to map preference topics to preference class attributes
preference_topic_to_value = {
    "CoValuePreference": "co2",
    "TempValuePreference": "temperature",
    "ambientNPreference": "noise",
    "lightSensePreference": "light",
    "windSensePreference": "wind",
}

@dataclass
class SensorState:
    #curr value of sensor
    curr_value: float
    #last value that was given to the planner
    last_plan_state_value: float = None

    def get_value_change(self):
        """calculates change of sensor value since the last planning step

        Returns:
            float: absolute change
        """
        return abs(self.curr_value-self.last_plan_state_value)

class LockedDict(dict):
    """Prevent the (very unlikely) concurrency errors, that may occur when writing multiple sensor values into a dict at the same time
    """
    def __init__(self):
        self.dict_lock = Lock()
        super().__init__()

    def update(self, *args, **kwargs):
        with self.dict_lock:
            super().update(*args, **kwargs)
    
    def pop(self, *args, **kwargs):
        with self.dict_lock:
            return super().pop(*args, **kwargs)

    def keys(self, *args, **kwargs):
        with self.dict_lock:
            return super().keys(*args, **kwargs)

    def get(self, *args, **kwargs):
        with self.dict_lock:
            return super().get(*args, **kwargs)

class DataService:
    def __init__(self) -> None:
        #sensor value
        self.temperature_ins: SensorState = SensorState(None)
        self.temperature_out: SensorState = SensorState(None)
        self.rain: SensorState = SensorState(None)
        self.co2: SensorState = SensorState(None)
        self.noise_data: LockedDict[str, SensorState] = LockedDict()
        self.wind_data: LockedDict[str, SensorState] = LockedDict()
        self.light_data: LockedDict[str, SensorState] = LockedDict()
        #actuator values
        self.heating_state: ActuatorState = ActuatorState("auto", "off")
        self.windowstates: LockedDict[str, ActuatorState] = LockedDict()
        self.blindstates: LockedDict[str, ActuatorState] = LockedDict()
        #preferences
        self.preferences = Preferences()
        self.init_mqtt_connection()

    def print_state(self):
        """prints current state of all connected devices
        """
        print("------- Sensors -------")
        print("Temperature inside is: ", self.temperature_ins.curr_value, "Last plan val is: ", self.temperature_ins.last_plan_state_value)
        print("Temperature outside is: ", self.temperature_out.curr_value, "Last plan val is: ", self.temperature_out.last_plan_state_value)
        print("Rain is: ", self.rain.curr_value, "Last plan val is: ", self.rain.last_plan_state_value)
        self.__print_sensor_dict("Noise", self.noise_data)
        self.__print_sensor_dict("Wind", self.wind_data)
        self.__print_sensor_dict("Light intensity", self.light_data)
        print("------- Actuators -------")
        self.__print_actuators()
        print("------- Preferences -------")
        print(self.preferences)

    def __print_actuators(self):
        #get and print state of all windows
        with self.windowstates.dict_lock:
            for location in self.windowstates:
                print(f"Window at location '{location}' is in mode: ", self.windowstates[location].operation_mode, "Current state of win is: ", self.windowstates[location].current_state)
        #get and print state of all blinds
        with self.blindstates.dict_lock:
            for location in self.blindstates:
                print(f"Blind at location '{location}' is in mode: ", self.blindstates[location].operation_mode, "Current state of blind is: ", self.blindstates[location].current_state)
        print(f"Heating is in mode: ", self.heating_state.operation_mode, "Current state of heating is: ", self.heating_state.current_state)
        

    def __print_sensor_dict(self, name: str, sensor_dict: LockedDict[str, SensorState]):
        #iterate over list of locatins for given sensor
        with sensor_dict.dict_lock:
            for location in sensor_dict:
                print(f"{name} at location '{location}' has val: ", sensor_dict[location].curr_value, "Last plan val is: ", sensor_dict[location].last_plan_state_value)

    def init_mqtt_connection(self):
        self.client = mqtt.Client(client_id=str(uuid.uuid1()))
        self.client.username_pw_set(username="iotproject", password="iotaccesspw%")
        self.client.on_message=self.on_message
        self.client.connect("82.165.70.137", 1884, 60)
        self.clientloop_thread = Thread(target=self.client.loop_forever, daemon=True)
        self.clientloop_thread.start()
        #subscribe to topic of sensors
        self.client.subscribe("sensors/#")
        #subscribe to topic of actuators
        self.client.subscribe("actuators/#")
        #subscribe to preferences
        self.client.subscribe("CoValuePreference")
        self.client.subscribe("TempValuePreference")
        self.client.subscribe("ambientNPreference")
        self.client.subscribe("lightSensePreference")
        self.client.subscribe("windSensePreference")

    def on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        topic_parts: list[str] = msg.topic.split("/")
        payload: str = msg.payload.decode("utf-8")
        print("message arrived topic is: ", msg.topic)
        if topic_parts[0] == "sensors":
            #message contains sensor information
            self.parse_sensor_msg(topic_parts[1:], payload)
        elif topic_parts[0] == "actuators":
            #message contains actuator information
            self.parse_act_msg(topic_parts[1:], payload)
        else:
            #message contains user preference information
            self.parse_pref_msg(topic_parts[0], payload)

    def parse_act_msg(self, act_topic_parts: str, payload: str):
        if act_topic_parts[0] == "windows":
            #handle window msg
            if act_topic_parts[1] in self.windowstates.keys():
                #check if message is empty if so remove actuator from list
                if payload == "":
                    self.windowstates.pop(act_topic_parts[1])
                elif act_topic_parts[2] == "status":
                    #otherwise update value
                    with self.windowstates.dict_lock:
                        self.windowstates[act_topic_parts[1]].current_state = payload
                elif act_topic_parts[2] == "mode":
                    #otherwise update value
                    with self.windowstates.dict_lock:
                        self.windowstates[act_topic_parts[1]].operation_mode = payload
            elif not payload == "" and act_topic_parts[2] == "status":
                self.windowstates.update({act_topic_parts[1]: ActuatorState("auto", payload)})
        elif act_topic_parts[0] == "blinds":
            #handle window msg
            if act_topic_parts[1] in self.blindstates.keys():
                #check if message is empty if so remove actuator from list
                if payload == "":
                    self.blindstates.pop(act_topic_parts[1])
                elif act_topic_parts[2] == "status":
                    #otherwise update value
                    with self.blindstates.dict_lock:
                        self.blindstates[act_topic_parts[1]].current_state = payload
                elif act_topic_parts[2] == "mode":
                    #otherwise update value
                    with self.blindstates.dict_lock:
                        self.blindstates[act_topic_parts[1]].operation_mode = payload
            elif not payload == "" and act_topic_parts[2] == "status":
                self.blindstates.update({act_topic_parts[1]: ActuatorState("auto", payload)})
        elif act_topic_parts[0] == "heating":
            #handle heating msg
            if act_topic_parts[1] == "status":
                self.heating_state.current_state = float(payload)
            elif act_topic_parts[1] == "mode":
                self.heating_state.operation_mode = payload

    def parse_pref_msg(self, topic: str, payload: str):
        payload = json.loads(payload)["data"]
        if topic in preference_topic_to_value:
            mapped_topic = preference_topic_to_value[topic]
            if mapped_topic == "temperature":
                if payload == "":
                    self.preferences.__dict__[mapped_topic] = [None, None]
                else:
                    self.preferences.__dict__[mapped_topic] = payload
            else:
                if payload == "":
                    self.preferences.__dict__[mapped_topic] = None
                else:
                    self.preferences.__dict__[mapped_topic] = payload

    def parse_sensor_msg(self, sensor_topic_parts: str, payload: str):
        #case temperature message
        if sensor_topic_parts[0] == "temperature":
            if sensor_topic_parts[1] == "inside":
                if not payload == "":
                    self.temperature_ins.curr_value = float(payload)
            elif sensor_topic_parts[1] == "outside":
                if not payload == "":
                    self.temperature_out.curr_value = float(payload)
            else:
                print("Unexpected location part for temperature sensors: ", sensor_topic_parts[1])
        #case noise message
        elif sensor_topic_parts[0] == "noise":
            #check if location already stored
            if sensor_topic_parts[1] in self.noise_data.keys():
                #check if message is empty if so remove sensor from list
                if payload == "":
                    self.noise_data.pop(sensor_topic_parts[1])
                else:
                    #otherwise update value
                    with self.noise_data.dict_lock:
                        self.noise_data[sensor_topic_parts[1]].curr_value = float(payload)
            elif not payload == "":
                #add new sensor
                self.noise_data.update({sensor_topic_parts[1]: SensorState(float(payload), 999)})
        elif sensor_topic_parts[0] == "wind":
            #check if location already stored
            if sensor_topic_parts[1] in self.wind_data.keys():
                #check if message is empty if so remove sensor from list
                if payload == "":
                    self.wind_data.pop(sensor_topic_parts[1])
                else:
                    #otherwise update value
                    with self.wind_data.dict_lock:
                        self.wind_data[sensor_topic_parts[1]].curr_value = float(payload)
            elif not payload == "":
                #add new sensor
                self.wind_data.update({sensor_topic_parts[1]: SensorState(float(payload), 999)})
        elif sensor_topic_parts[0] == "sun":
            #check if location already stored
            if sensor_topic_parts[1] in self.light_data.keys():
                #check if message is empty if so remove sensor from list
                if payload == "":
                    self.light_data.pop(sensor_topic_parts[1])
                else:
                    #otherwise update value
                    with self.light_data.dict_lock:
                        self.light_data[sensor_topic_parts[1]].curr_value = float(payload)
            elif not payload == "":
                #add new sensor
                self.light_data.update({sensor_topic_parts[1]: SensorState(float(payload), 999)})
        elif sensor_topic_parts[0] == "rain":
            #check if location already stored
            if not payload == "":
                self.rain.curr_value = float(payload)
            else:
                self.rain.curr_value = None
        elif sensor_topic_parts[0] == "CO2":
            #check if location already stored
            if not payload == "":
                self.co2.curr_value = float(payload)
            else:
                self.co2.curr_value = None

class ManagePlanner:
    """creates problem file for planner and manages when to execute the planenr
    """
    def __init__(self) -> None:
        pass

    def execute_planner(self):
        self.create_planner_problem()
        #call actual planner and parse output
    
    def create_planner_problem(self):
        pass
# %%
data = DataService()
#%%
input()