#%%
from abc import ABC, abstractmethod
import cmd
import datetime as dt
from threading import Thread
import numpy as np
import paho.mqtt.client as mqtt
import uuid
import random
import time

class Sensor(ABC):
    def __init__(self, simulation_interval: int=15) -> None:
        """Initialises mqtt connection for sensor and simulation loop

        Args:
            simulation_interval (int, optional): Interval at which to simulate value change in seconds. Defaults to 15.
        """
        self.simulation_interval: int = simulation_interval
        self.lastsimulation: dt.datetime = dt.datetime.now()
        self.init_sensor_mqtt()
        self.simulation_thread: Thread = Thread(target=self.simulation_loop, daemon=True)
        self.simulation_thread.start()
    def simulation_loop(self):
        while True:
            self.publish_value()
            time.sleep(self.simulation_interval)
            self.simulate_value()
            
    def publish_value(self):
        if self.location:
            self.client.publish(f"sensors/{self.type}/{self.location}", payload="{:.2f}".format(self.value), qos=1, retain=True)
        else:
            self.client.publish(f"sensors/{self.type}", payload="{:.2f}".format(self.value), qos=1, retain=True)
    @property
    @abstractmethod
    def type(self): 
        return NotImplementedError
    @property
    @abstractmethod
    def location(self): 
        return NotImplementedError
    @property
    @abstractmethod
    def value(self): 
        return NotImplementedError
    @abstractmethod
    def simulate_value(self): 
        return NotImplementedError
    def __str__(self) -> str:
        return str(self.type) + str(self.location) 
    def get_simulation_delta_time(self):
        """calculates time delta since last simulation in minutes
        Returns: float: minutes since last simulation
        """        
        return (dt.datetime.now()-self.lastsimulation).total_seconds()/60
    def init_sensor_mqtt(self):
        self.client = mqtt.Client(client_id=str(uuid.uuid1()))
        self.client.username_pw_set(username="iotproject", password="iotaccesspw%")
        if self.location:
            self.client.will_set(f"sensors/{self.type}/{self.location}", payload="", qos=1, retain=True)
        else:
            self.client.will_set(f"sensors/{self.type}", payload="", qos=1, retain=True)
        self.client.connect("82.165.70.137", 1884, 60)
        self.clientloop_thread = Thread(target=self.client.loop_forever, daemon=True)
        self.clientloop_thread.start()

class DataService():
    def __init__(self) -> None:
        self.init_mqtt()
        self.outside_temp = None
        self.windows: dict[str, str] = {}
        self.heating_power = None

    def init_mqtt(self):
        self.client = mqtt.Client(client_id=str(uuid.uuid1()))
        self.client.username_pw_set(username="iotproject", password="iotaccesspw%")
        self.client.on_message=self.on_message
        self.client.connect("82.165.70.137", 1884, 60)
        self.clientloop_thread = Thread(target=self.client.loop_forever, daemon=True)
        self.clientloop_thread.start()
        self.client.subscribe("sensors/temperature/outside")
        self.client.subscribe("actuators/windows/+/status")
        #change power to status power only used to debug
        self.client.subscribe("actuators/heating/power")

    def on_message(self, client, userdata, msg):
        if msg.topic == "sensors/temperature/outside":
            self.outside_temp = float(msg.payload.decode("utf-8"))
        elif msg.topic.startswith("actuators/windows/"):
            location = msg.topic[18:-7]
            self.windows[location] = str(msg.payload.decode("utf-8"))
        elif msg.topic == "actuators/heating/power":
            self.heating_power = float(msg.payload.decode("utf-8"))

class TemperatureSensor(Sensor):
    def __init__(self, init_value=20, inside: bool=False, dataService: DataService=None, simulation_interval: int=3) -> None:
        self._type="temperature"
        self._value = init_value
        self._location = ["outside", "inside"][inside]
        self.dataService = dataService
        self.change_per_minute = 0.1
        self.max_heater_temp = 40
        if inside and not dataService:
            raise UserWarning("Inside sensor initialized without datasource")
        super().__init__(simulation_interval=simulation_interval)

    @property
    def type(self):
        return self._type

    @property
    def location(self):
        return self._location
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def simulate_value(self):
        if self.location == "inside":
            self.simulate_inside()
        else:
            self.simulate_outside()

    def simulate_inside(self):
        tdelta = self.get_simulation_delta_time()
        if self.dataService.outside_temp:
            #temperature value is slowly drawn to outside temperature
            self.value += (self.dataService.outside_temp-self.value)*0.01*tdelta
            #effect of open windows
            num_open_win = sum(map(lambda win: int(win=="open"), self.dataService.windows.values()))
            self.value += (self.dataService.outside_temp-self.value)*0.07*tdelta*num_open_win
            #effect of heating
            if self.dataService.heating_power:
                self.value += (self.max_heater_temp-self.value)*tdelta*0.8*self.dataService.heating_power
        self.lastsimulation = dt.datetime.now()

    def simulate_outside(self):
        """simulates temperature change over time
        temperature range is limited to [-15, 50]
        """
        tdelta = self.get_simulation_delta_time()
        self.value = max(-15, min(self.value+np.random.uniform(-self.change_per_minute*tdelta, self.change_per_minute*tdelta),50))
        self.lastsimulation = dt.datetime.now()



class WindSensor(Sensor):
    def __init__(self, location: str, init_value=5, dataService=None, simulation_interval: int=3) -> None:
        self._type="wind"
        #wind speed in mph
        self.value = init_value
        self._location = location
        self.dataService = dataService
        self.lastsimulation: dt.datetime = dt.datetime.now()
        self.change_per_minute = 4
        super().__init__(simulation_interval=simulation_interval)

    @property
    def type(self):
        return self._type

    @property
    def location(self):
        return self._location
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def simulate_value(self):
        """simulates wind speed change over time
        wind speed range is limited to [0, 100]
        """
        tdelta = self.get_simulation_delta_time()
        self.value = max(0, min(self.value+np.random.uniform(-self.change_per_minute*tdelta, self.change_per_minute*tdelta),100))
        self.lastsimulation = dt.datetime.now()

class NoiseSensor(Sensor):
    def __init__(self, location: str, init_value=50, dataService=None, simulation_interval: int=3) -> None:
        self._type="noise"
        #noise in decibels
        self.value = init_value
        self._location = location
        self.dataService = dataService
        self.lastsimulation: dt.datetime = dt.datetime.now()
        self.change_per_minute = 4
        super().__init__(simulation_interval=simulation_interval)

    @property
    def type(self):
        return self._type

    @property
    def location(self):
        return self._location
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def simulate_value(self):
        """simulates noise change over time
        noise range is limited to [30, 110] decibels
        """
        tdelta = self.get_simulation_delta_time()
        self.value = max(30, min(self.value+np.random.uniform(-self.change_per_minute*tdelta, self.change_per_minute*tdelta),110))
        self.lastsimulation = dt.datetime.now()

class CoSensor(Sensor):
    def __init__(self, dataService: DataService, init_value=700, simulation_interval: int=3) -> None:
        self._type="CO2"
        #value in ppm
        self._value = init_value
        self._location = "inside"
        self.dataService = dataService
        self.change_per_minute = 15
        self.window_impact = 20
        super().__init__(simulation_interval=simulation_interval)

    @property
    def type(self):
        return self._type

    @property
    def location(self):
        return self._location
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def simulate_value(self):
        """simulates co2 level change over time
        co2 range is limited to [200, 20000] decibels
        """
        tdelta = self.get_simulation_delta_time()
        #co2 increase over time
        self.value += tdelta*self.change_per_minute*random.random()
        #co2 decrease by open windows
        #get number of open windows
        num_open_win = sum(map(lambda win: int(win=="open"), self.dataService.windows.values()))
        self.value -= tdelta*self.window_impact*random.random()*num_open_win
        self.value = min(20000, max(200, self.value))
        self.lastsimulation = dt.datetime.now()
        


    
# %%
data = DataService()
out_temp = TemperatureSensor()
in_temp = TemperatureSensor(25, True, data)
noise_east = NoiseSensor("east")
noise_west = NoiseSensor("west")
wind = WindSensor("outside")
co = CoSensor(data)

sensor_list: Sensor = [out_temp, in_temp, noise_east, noise_west, wind, co]
# %%
def show_status():
        status = ""
        for sensor in sensor_list:
            stat_string = f"Type: {sensor.type} Location: {sensor.location} Current val: {str(sensor.value)[:str(sensor.value).find('.')+3]}\n"
            status += stat_string
        print(status)

# %%

def nofail(f):
    def save_exec(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(e)
    return save_exec

class cli(cmd.Cmd):
    prompt = "> "

    def do_status(self, line):
        """status
        -display the status of the simulated sensors"""
        show_status()

    @nofail
    def do_outsidetemp(self, line):
        """outsidetemp [temp]
        -set outside temp sensor to given value"""
        out_temp.value = float(line.split(" ")[-1])

    @nofail
    def do_insidetemp(self, line):
        """insidetemp [temp]
        -set inside temp sensor to given value"""
        in_temp.value = float(line.split(" ")[-1])

    @nofail
    def do_windspeed(self, line):
        """windspeed [value]
        -set windspeed to value"""
        wind.value = float(line.split(" ")[-1])

    @nofail
    def do_co2conc(self, line):
        """co2conc [value]
        -set co2 concentration to value"""
        co.value = float(line.split(" ")[-1])
    
    @nofail
    def do_noisevol(self, line):
        """noisevol [location] [value]
        -set noise vol of location to value"""
        location, value = line.split(" ")[-2], line.split(" ")[-1]
        for i in sensor_list:
            if isinstance(i, NoiseSensor) and i.location == location:
                i.value = float(value)
                return None
        print("No noise location found for location:", location)

    def do_clear(self, line):
        """clears the screen"""
        print("\033[H\033[J")

    def do_quit(self, line):
        """ends the program"""
        quit()

if __name__ == '__main__':
    cli().cmdloop()