#%%
import os
from typing import List, Union
import paho.mqtt.client as mqtt
import uuid
import json
from threading import Thread, Lock, Event, Timer
from dataclasses import dataclass, field
import datetime as dt

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
    previous states are not saved, because any change will trigger a planner action
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
    def change_above_threshold(self, threshold):
        return self.get_value_change() > threshold

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
    def __init__(self, planmgr) -> None:
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
        #assign manager to service that gets notified about data changes 
        self.planmgr = planmgr
        #register this DataService as data source for manager
        planmgr.registerDataService(self)
        #initialize mqtt connection and loop
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
        #check if topic is a valid preference
        if topic in preference_topic_to_value:
            #map to local var representing preference
            mapped_topic = preference_topic_to_value[topic]
            #tempereature is handled separate because it has a different delete state [None, None]
            if mapped_topic == "temperature":
                if payload == "":
                    self.preferences.__dict__[mapped_topic] = [None, None]
                else:
                    self.preferences.__dict__[mapped_topic] = payload
            #handle everything else
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
    
    def get_windowstates(self):
        """retrieves all windows that should be considered during planning

        Returns:
            dict[str, str]: returns dict with location and current status
        """
        windows: dict = dict()
        #iterate over all windows
        with self.windowstates.dict_lock:
            for windowlocation in self.windowstates:
                #check if window is set to automated mode
                if self.windowstates[windowlocation].operation_mode == "auto":
                    #if so add to result
                    windows[windowlocation] = self.windowstates[windowlocation].current_state
        return windows

class PlanActionMgr:
    """creates problem file for planner and manages when to execute the planner
    """
    def __init__(self, mtbp_actions: int) -> None:
        """initializes variables and planner thread 
        Args:
            mtbp_actions (int): specify the minimal time between to planning actions in seconds
        """
        #min time between planning actions
        self.mtbp_actions: int = mtbp_actions
        #last time planner was called init with future value to allow for initialization time
        self.last_action_time: dt.datetime = dt.datetime.now()+dt.timedelta(seconds=mtbp_actions*0.8)
        #event used to signal if planning is required
        self.planning_req: Event = Event()
        #set event to true to run planner 1 time initially
        self.planning_req.set()
        #flag to track if a timer to start planning action as soon as possible has been set 
        #--> avoid setting multiple timers
        self.delayed_timer_set: bool = False
        #lock to sync access to the delayed timer flag
        self.timer_set_lock: Lock = Lock()
        #initialize empty data service
        self.data: DataService = None

    def registerDataService(self, dataS: DataService):
        #set data service
        self.data = dataS
        #allow for init time
        self.last_action_time: dt.datetime = dt.datetime.now()+dt.timedelta(seconds=self.mtbp_actions*0.8)
        #start planning loop
        self.planning_thread = Thread(target=self.planning_loop, daemon=True)
        self.planning_thread.start()

    def planning_loop(self):
        print("loop started")
        #loop forever
        while True:
            #wait until a planning action is required --> saves resources
            self.planning_req.wait()
            #start with setting last planning action time to now 
            #do this since there is no gurantee that changes arriving during this planning phase will be reflected in result
            self.last_action_time = dt.datetime.now()
            self.planning_req.clear()
            #create problem for planner
            self.create_planner_problem()


    def notify(self) -> None:
        """notifies thread that changes have occured and allows planner to plan
        if the minimal amount of time between planning actions has not passed yet __notify_delayed will be called
        """
        #time delta since last action in seconds
        action_time_delta = (dt.datetime.now-self.last_action_time).total_seconds()
        #if time passed since last action is bigger than minimum time between actions
        #AND no timer is set that would trigger planner anyway --> trigger planner
        if action_time_delta > self.mtbp_actions and not self.checkTimerSet():
            self.planning_req.set()
        else:
            #otherwise trigger planner once it becomes available
            self.__notify_delayed(abs(action_time_delta - self.mtbp_actions))
        

    def __notify_delayed(self, delay: float) -> None:
        """sets time to call notify after delay 
            makes sure that only one timer may exist at once
        Args:
            delay (float): delay until notify call in seconds
        """
        with self.timer_set_lock:
            if self.delayed_timer_set == False:
                self.setTimer(delay)

    def setTimer(self, delay):
            t = Timer(delay, self.triggerTimer)
            t.start()
            self.delayed_timer_set = True

    def triggerTimer(self):
        with self.timer_set_lock:
            self.delayed_timer_set = False
        self.notify()

    def checkTimerSet(self) -> bool:
        with self.timer_set_lock:
            return self.delayed_timer_set

    def execute_planner(self):
        self.create_planner_problem()
        #call actual planner and parse output
    
    def create_planner_problem(self):
        dirname, filename = os.path.split(os.path.abspath(__file__))
        #read in the problem template
        with open(dirname+"/problem_template.pddl") as f:
            p_template: str = f.read()
        #vars used to later on generate problem
        objects_part: dict = dict()
        init_part: dict = dict()
        goal_part: dict = dict()
        #gather window data
        windows: dict = self.data.get_windowstates()
        #begin replacing necessary variables
        #start with objects

        
# %%
mgr = PlanActionMgr()
data = DataService(mgr)
#%% 
input()