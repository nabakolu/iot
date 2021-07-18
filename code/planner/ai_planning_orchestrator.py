#%%
import os
from typing import List, Union
import paho.mqtt.client as mqtt
import uuid
import json
from threading import Thread, Lock, Event, Timer
from dataclasses import dataclass, field
import datetime as dt
import math
import subprocess
from execute_solution import execute_solution

#thresholds for maximum change that can occur to a value before recalculation is triggered
CHANGE_THRESHOLDS = {"temperature": 1.5, "co2": 40,"noise": 2, "wind": 1.5, "sun": 150, "rain": 0.5}
#importance of outside influences for the decicion to operate the window
INFLUENCE_IMPORTANCE = {"co2": 3, "noise": 1, "wind": 1, "rain": 1.5}

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
    def copy(self):
        return Preferences(self.co2, self.light, self.noise, self.wind, [self.temperature[0], self.temperature[1]])

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
    last_plan_state_value: float = 9999

    def get_value_change(self):
        """calculates change of sensor value since the last planning step

        Returns:
            float: absolute change
        """
        return abs(self.curr_value-self.last_plan_state_value)
    def change_above_threshold(self, threshold):
        if self.curr_value != None and self.last_plan_state_value != None:
            return self.get_value_change() > threshold
        else:
            return True

    def get_plan_value(self) -> float:
        r_value, self.last_plan_state_value = self.curr_value, self.curr_value
        return r_value

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
        self.heating_state: ActuatorState = ActuatorState("auto", 0)
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
        

    def __print_sensor_dict(self, name: str, sensor_dict):
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
        #print("message arrived topic is: ", msg.topic)
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
                    #if an actuator get deleted --> notify plan manager
                    self.planmgr.notify()
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
                    #if an actuator get deleted --> notify plan manager
                    self.planmgr.notify()
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
                if payload == "":
                    payload = 0
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
            self.planmgr.notify()

    def parse_sensor_msg(self, sensor_topic_parts: str, payload: str):
        #case temperature message
        if sensor_topic_parts[0] == "temperature":
            if sensor_topic_parts[1] == "inside":
                if not payload == "":
                    self.temperature_ins.curr_value = float(payload)
                    if self.temperature_ins.change_above_threshold(CHANGE_THRESHOLDS["temperature"]):
                        self.planmgr.notify()
            elif sensor_topic_parts[1] == "outside":
                if not payload == "":
                    self.temperature_out.curr_value = float(payload)
                    if self.temperature_out.change_above_threshold(CHANGE_THRESHOLDS["temperature"]):
                        self.planmgr.notify()
            else:
                print("Unexpected location part for temperature sensors: ", sensor_topic_parts[1])
        #case noise message
        elif sensor_topic_parts[0] == "noise":
            #check if location already stored
            if sensor_topic_parts[1] in self.noise_data.keys():
                #check if message is empty if so remove sensor from list
                if payload == "":
                    self.noise_data.pop(sensor_topic_parts[1])
                    #if a sensor gets deleted --> notify plan manager
                    self.planmgr.notify()
                else:
                    #otherwise update value
                    with self.noise_data.dict_lock:
                        self.noise_data[sensor_topic_parts[1]].curr_value = float(payload)
                        if self.noise_data[sensor_topic_parts[1]].change_above_threshold(CHANGE_THRESHOLDS["noise"]):
                            self.planmgr.notify()
            elif not payload == "":
                #add new sensor
                self.noise_data.update({sensor_topic_parts[1]: SensorState(float(payload), 999)})
                #if a sensor gets added --> notify plan manager
                self.planmgr.notify()
        elif sensor_topic_parts[0] == "wind":
            #check if location already stored
            if sensor_topic_parts[1] in self.wind_data.keys():
                #check if message is empty if so remove sensor from list
                if payload == "":
                    self.wind_data.pop(sensor_topic_parts[1])
                    #if a sensor gets deleted --> notify plan manager
                    self.planmgr.notify()
                else:
                    #otherwise update value
                    with self.wind_data.dict_lock:
                        self.wind_data[sensor_topic_parts[1]].curr_value = float(payload)
                        if self.wind_data[sensor_topic_parts[1]].change_above_threshold(CHANGE_THRESHOLDS["wind"]):
                            self.planmgr.notify()
            elif not payload == "":
                #add new sensor
                self.wind_data.update({sensor_topic_parts[1]: SensorState(float(payload), 999)})
                #if a sensor gets added --> notify plan manager
                self.planmgr.notify()
        elif sensor_topic_parts[0] == "sun":
            #check if location already stored
            if sensor_topic_parts[1] in self.light_data.keys():
                #check if message is empty if so remove sensor from list
                if payload == "":
                    self.light_data.pop(sensor_topic_parts[1])
                    #if a sensor gets deleted --> notify plan manager
                    self.planmgr.notify()
                else:
                    #otherwise update value
                    with self.light_data.dict_lock:
                        self.light_data[sensor_topic_parts[1]].curr_value = float(payload)
                        if self.light_data[sensor_topic_parts[1]].change_above_threshold(CHANGE_THRESHOLDS["sun"]):
                            self.planmgr.notify()
            elif not payload == "":
                #add new sensor
                self.light_data.update({sensor_topic_parts[1]: SensorState(float(payload), 999)})
                #if a sensor gets added --> notify plan manager
                self.planmgr.notify()
        elif sensor_topic_parts[0] == "rain":
            #check if location already stored
            if not payload == "":
                self.rain.curr_value = float(payload)
                if self.rain.change_above_threshold(CHANGE_THRESHOLDS["rain"]):
                    self.planmgr.notify()
            else:
                self.rain.curr_value = None
                #if a sensor gets deleted --> notify plan manager
                self.planmgr.notify()
        elif sensor_topic_parts[0] == "CO2":
            #check if location already stored
            if not payload == "":
                self.co2.curr_value = float(payload)
                if self.co2.change_above_threshold(CHANGE_THRESHOLDS["co2"]):
                    self.planmgr.notify()
            else:
                self.co2.curr_value = None
                #if a sensor gets deleted --> notify plan manager
                self.planmgr.notify()
    
    def get_windowstates(self) -> dict:
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
    
    def get_blindstate(self) -> dict:
        """retrieves all blinds that should be considered during planning

        Returns:
            dict[str, str]: returns dict with location and current status
        """
        blinds: dict = dict()
        #iterate over all blinds
        with self.blindstates.dict_lock:
            for blindlocation in self.blindstates:
                #check if blind is set to automated mode
                if self.blindstates[blindlocation].operation_mode == "auto":
                    #if so add to result
                    blinds[blindlocation] = self.blindstates[blindlocation].current_state
        return blinds
    
    def get_heating(self) -> float:
        if self.heating_state.operation_mode == "auto":
            return self.heating_state
        else:
            return None

    def get_sensors(self):
        """returns sensor information that should be used for planning step

        Returns:
            dict[str, dict[str, float]]: a dict with key sensor locations and value dict with sensor types as keys
        """
        sensors: dict[str, dict[str, str]] = dict()
        #get noise data
        with self.noise_data.dict_lock:
            for location in self.noise_data:
                if sensors.get(location):
                    sensors[location].update({"ambientnoise": self.noise_data[location].get_plan_value()})
                else:
                    sensors[location] = {"ambientnoise": self.noise_data[location].get_plan_value()}
        #get wind data
        with self.wind_data.dict_lock:
            for location in self.wind_data:
                if sensors.get(location):
                    sensors[location].update({"wind": self.wind_data[location].get_plan_value()})
                else:
                    sensors[location] = {"wind": self.wind_data[location].get_plan_value()}
        #get light
        with self.light_data.dict_lock:
            for location in self.light_data:
                if sensors.get(location):
                    sensors[location].update({"light": self.light_data[location].get_plan_value()})
                else:
                    sensors[location] = {"light": self.light_data[location].get_plan_value()}
        #all unique sensor readings that are not location dependent
        temp_ins= self.temperature_ins.get_plan_value()
        temp_out = self.temperature_out.get_plan_value()
        rain = self.rain.get_plan_value()
        co2 = self.co2.get_plan_value()
        return sensors, temp_ins, temp_out, rain, co2

    def get_preferences(self) -> Preferences:
        """generates and returns a value copy of the current preferences

        Returns:
            Preferences: copy of the preferences
        """
        return self.preferences.copy()

class PlanActionMgr:
    """creates problem file for planner and manages when to execute the planner
    """
    def __init__(self, mtbp_actions: int = 3) -> None:
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
        #flag to track if a timer to start planning action as soon as possible has been set 
        #--> avoid setting multiple timers
        self.delayed_timer_set: bool = False
        #lock to sync access to the delayed timer flag
        self.timer_set_lock: Lock = Lock()
        #initialize empty data service
        self.data: DataService = None
        self.logvar = []

    def registerDataService(self, dataS: DataService):
        #set data service
        self.data = dataS
        #allow for init time
        self.last_action_time: dt.datetime = dt.datetime.now()+dt.timedelta(seconds=self.mtbp_actions*0.8)
        #run planner 1 time initially
        self.notify()
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
            temp_ins, max_temp = self.create_planner_problem()
            self.execute_planner(temp_ins, max_temp)


    def notify(self) -> None:
        """notifies thread that changes have occured and allows planner to plan
        if the minimal amount of time between planning actions has not passed yet __notify_delayed will be called
        """
        #time delta since last action in seconds
        action_time_delta = (dt.datetime.now()-self.last_action_time).total_seconds()
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

    def execute_planner(self, temp_ins: float, max_temp: float):
        #call actual planner
        cmd = "wsl.exe optic-clp window-domain.pddl output_template.pddl"
        p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #if len(p.stderr) != 0:
            #print("!!!Planner stderr not empty:\n", p.stderr)
        #execute found solution
        try:
            print("")
            print(p.stdout.decode("utf-8")[p.stdout.decode("utf-8").find(";;;; Solution Found"):])
            execute_solution(p.stdout.decode("utf-8") , self.data.client, temp_ins, max_temp)
        except Exception as e:
            print("Exception in execute_solution():\n", e)
            #print(p.stdout)
        
    
    def create_planner_problem(self):
        self.logvar.append("creating planner problem")
        #vars used to later on generate problem
        objects_part: dict = dict()
        init_part: dict = dict()
        goal_part: dict = dict()
        #gather window data
        windows: dict = self.data.get_windowstates()
        #gather blind data
        blinds: dict = self.data.get_blindstate()
        #gather heating data
        heating: dict = self.data.get_heating()
        #gather sensor data
        sensors, temp_ins, temp_out, rain, co2 = self.data.get_sensors()
        #get preferences
        preferences: Preferences = self.data.get_preferences()
        self.planning_req.clear()
        #read in the problem template
        dirname, filename = os.path.split(os.path.abspath(__file__))
        with open(dirname+"/problem_template.pddl", "r") as f:
            p_template: str = f.read()
        #begin replacing necessary variables
        #start with generating objects
        p_template = self.generate_objects(p_template, windows, blinds)
        #generate init
        p_template = self.generate_init_part(p_template, windows, blinds, sensors, temp_ins, temp_out, rain, co2, preferences, heating)
        #generate goal
        p_template = self.generate_goal_part(p_template, windows, blinds, heating)
        #write problem file
        with open(dirname+"/output_template.pddl", "w") as f:
            f.write(p_template)
        return temp_ins, preferences.temperature[1]

    def generate_goal_part(self, p_template, windows, blinds, heating) -> str:
        r_str = "(and\n"
        for location in blinds:
            r_str += self.generate_problem_predicate("not_blinding", "blind_"+location)
            r_str += self.generate_goal_preference("blindsOpen", "open", "blind_"+location)
        for location in windows:
            r_str += self.generate_goal_preference("windowsOpen", "open", "window_"+location)
        #TODO recomment for final
        #if heating != None:
        r_str += self.generate_goal_preference("heaterPref", "heater_off", "central_heater")
        r_str += self.generate_goal_preference("heaterPref", "heater_on", "central_heater")
        r_str += ")\n"
        return p_template.replace(";[goal-template-string]", r_str)

    def generate_goal_preference(self, name, predicate, obj) -> str:
        r_str = f"(preference {name}\n"
        r_str += "  "+self.generate_problem_predicate(predicate, obj)
        r_str += ")\n"
        return r_str

    def generate_objects(self, template: str, windows, blinds) -> str:
        """places 

        Args:
            template (str): [description]
            windows ([type]): [description]
            blinds ([type]): [description]

        Returns:
            str: [description]
        """
        object_str = ""
        #generate windows
        for loc in windows:
            object_str += " window_"+loc
        object_str += " - window\n"
        #generate blinds
        for loc in blinds:
            object_str += " blind_"+loc
        object_str += " - blind\n"
        #append heater (constant location)
        object_str += "central_heater - heater\n"
        return template.replace(";[objects-template-string]", object_str)

    def generate_init_part(self, template: str, windows, blinds, sensors, temp_ins, temp_out, rain, co2, preferences: Preferences, heating: float) -> str:
        self.logvar.append("generate init part")
        self.logvar.append((windows, blinds, sensors, temp_ins, temp_out, rain, co2))
        self.logvar.append(data.blindstates)
        r_str = ""
        #generate co2 value
        r_str += f"(= (co2) {self.map_co2_to_val(co2, preferences.co2 ,INFLUENCE_IMPORTANCE['co2'])})\n"
        for location in windows:
            if not windows[location] in [None, " ", ""]:
                #add window state vars
                r_str += self.generate_problem_predicate(windows[location], "window_"+location)
                r_str += self.generate_problem_predicate("action_available", "window_"+location)
                #add window specific sensor vars
                r_str += self.generate_window_sensor_vals(location, sensors, preferences, rain)
        for location in blinds:
            if not blinds[location] in [None, " ", ""]:
                #add window state vars
                r_str += self.generate_problem_predicate(blinds[location], "blind_"+location)
                if blinds[location] == "open":
                    r_str += self.generate_blinding_state(location, sensors, preferences.light)
                else:
                    r_str += self.generate_blinding_state(location, sensors, "disabled")
        #TODO recomment in for final release
        #if heating != None:
        r_str += self.generate_heater(temp_ins, temp_out, heating, preferences)
        return template.replace(";[init-template-string]", r_str)
            

    def generate_problem_function(self, function, obj, value) -> str:
        """creates string to initialize a function value for the problem pddl file"""
        return f"(= ({function} {obj}) {value})\n"

    def generate_problem_predicate(self, predicate, obj) -> str:
        """creates predicate init string for problem pddl file"""
        return f"({predicate} {obj})\n"

    def generate_blinding_state(self, location: str, sensors: dict, light_pref: str) -> str:
        """generates blind state for for a blind object within the pddl problem

        Args:
            location (str): location of blind
            sensors (dict): sensor information
            light_pref (str): user preference for light

        Returns:
            str: pddl blinding predicate string for blind at location
        """
        #pre high --> light > 0.4*1024 --> blinding
        #pre med --> light > 0.6*1024 --> blinding
        #pre low --> light > 0.8*1024 --> blinding
        blind_str = ""
        blinding = False
        #userpref for light sensitivity disabled or no sensor present --> not blinding
        if not sensors.get(location) or not sensors.get(location).get("light") or light_pref == "disabled":
            pass
        elif light_pref == "low":
            if sensors.get(location).get("light") > 0.8*1024:
                blinding = True
        elif light_pref == "mid":
            if sensors.get(location).get("light") > 0.6*1024:
                blinding = True
        elif light_pref == "high":
            if sensors.get(location).get("light") > 0.4*1024:
                blinding = True
        if blinding:
            blind_str += self.generate_problem_predicate("blinding", "blind_"+location)
        else:
            blind_str += self.generate_problem_predicate("not_blinding", "blind_"+location)
            blind_str += self.generate_problem_predicate("not_blinding_initial", "blind_"+location)
        return blind_str
    
    def generate_heater(self, temp_ins, temp_out, heating, preferences: Preferences):
        # weight += (min_temp-curr_temp) --> belohnung heizung an
        # 
        # weight += ?windows_open(0|1) * abs(outdoor_temp-curr_temp) --> belohnung heizung aus
        #
        #belohnung weil zu kalt - wenn fenster offen ist: bestrafung abstand ausentemperatur
        r_str = ""
        r_str += self.generate_problem_predicate("heater_action_available", "central_heater")
        if heating == 0:
            r_str += self.generate_problem_predicate("heater_off", "central_heater")
        else:
            r_str += self.generate_problem_predicate("heater_on", "central_heater")
        #calc diff temp inside to to min_temp
        min_temp = preferences.temperature[0]
        if min_temp != None and temp_ins != None and temp_out != None:
            r_str += self.generate_problem_function("min_temp", "central_heater", min_temp)
            r_str += self.generate_problem_function("curr_temp", "central_heater", temp_ins)
            r_str += self.generate_problem_function("temperatureDiffMinimum", "central_heater", min_temp-temp_ins)
            r_str += self.generate_problem_function("temperatureDiffOutside", "central_heater", abs(temp_out-temp_ins))
        return r_str


    def windows_open_close(self):
        #(+ co2value (- 1 (+ (ambientnoise ?window) (+ (wind ?window) (rain ?window))))))
        # weight += 1 -(noise+wind+rain)
        #co2 --> (user_pref, value)
            #user_pref --> poor, fair, average, good excellent
            #value --> min 200 max 20000
        #noise --> (noise_pref, noise_val)
            #noise user val --> disabled, low, mid, high
            #min 30 max 110
        #wind --> (wind_pref, wind_val)
            #wind user val --> disabled, low, mid, high
            #min 0 max 100
        #rain --> 0,1
        #!!!paper to justify ranges
        #https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8631933
        #-----------------------------------------------------------------------
        #3map(co2) - 1map(noise)-1map(wind)-1.5map(rain)
        pass

    def generate_window_sensor_vals(self, location: str, sensors: dict, preferences: Preferences, rain):
        #check if location in sensors
        r_str = ""
        sensors_at_location = sensors.get(location)
        if sensors_at_location:
            #if wind sensor is present at location
            if "wind" in sensors_at_location:
                r_str += self.generate_problem_function("wind", "window_"+location, self.map_wind_to_val(sensors_at_location["wind"], preferences.wind, INFLUENCE_IMPORTANCE["wind"]))
            #if noise sensor is present at location
            if "ambientnoise" in sensors_at_location:
                r_str += self.generate_problem_function("ambientnoise", "window_"+location, self.map_noise_to_val(sensors_at_location["ambientnoise"], preferences.noise, INFLUENCE_IMPORTANCE["noise"]))
            #if rain sensor is present
            if rain != None:
                r_str += self.generate_problem_function("rain", "window_"+location,  rain*INFLUENCE_IMPORTANCE["noise"])
        return r_str


    def map_co2_to_val(self, co2, pref, weight) -> float:
        #!!!paper to justify ranges
        #https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8631933
        if not co2:
            return None
        pref_ranges = {5: [200, 250], 4: [350, 1000], 3: [1000, 2000], 2: [2000, 5000], 1: [5000, 10000]}
        value_range = pref_ranges[pref]
        if co2 < value_range[0]:
            return 0
        elif co2 < value_range[1]:
            return (co2-value_range[0])/(value_range[1]-value_range[0])*weight
        else:
            return weight

    def map_noise_to_val(self, noise, pref, weight) -> float:
        #!!!gov site to justify ranges https://www.cdc.gov/nceh/hearing_loss/what_noises_cause_hearing_loss.html
        pref_ranges = {"high": [30, 70], "mid": [70, 85], "low": [85, 100], "disabled": [math.inf,math.inf]}
        value_range = pref_ranges[pref]
        if noise < value_range[0]:
            return 0
        elif noise < value_range[1]:
            return (noise-value_range[0])/(value_range[1]-value_range[0])*weight
        else:
            return weight

    def map_wind_to_val(self, wind, pref, weight) -> float:
        #beaufort scale wiki
        pref_ranges = {"high": [0, 5], "mid": [5, 20], "low": [20, 40], "disabled": [math.inf,math.inf]}
        value_range = pref_ranges[pref]
        if wind < value_range[0]:
            return 0
        elif wind < value_range[1]:
            return (wind-value_range[0])/(value_range[1]-value_range[0])*weight
        else:
            return weight

# %%
mgr = PlanActionMgr()
data = DataService(mgr)
#%% 
input()
#%%
# def map_co2_to_val(co2, pref, weight=3):
#     #!!!paper to justify ranges
#     #https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8631933
#     pref_ranges = {4: [200-250], 3: [350, 1000], 2: [1000, 2000], 1: [2000, 5000], 0: [5000, 10000]}
#     value_range = pref_ranges[pref]
#     if co2 < value_range[0]:
#         return 0
#     elif co2 < value_range[1]:
#         return (co2-value_range[0])/(value_range[1]-value_range[0])*weight
#     else:
#         return weight