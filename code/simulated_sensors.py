#%%
from abc import ABC, abstractmethod
import datetime as dt
from threading import Thread
import numpy as np
import paho.mqtt.client as mqtt
import uuid
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
            self.client.publish(f"sensors/{self.type}/{self.location}", payload=self.value, qos=1, retain=True)
        else:
            self.client.publish(f"sensors/{self.type}", payload=self.value, qos=1, retain=True)
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
        self.clientloop_thread = Thread(target=self.client.connect, daemon=True, args=("82.165.70.137", 1884, 60))
        self.clientloop_thread.start()

class TemperatureSensor(Sensor):
    def __init__(self, init_value=20, inside: bool=False, dataService=None, simulation_interval: int=3) -> None:
        self._type="temperature"
        self._value = init_value
        self._location = ["outside", "inside"][inside]
        self.dataService = dataService
        self.change_per_minute = 0.1
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
        pass

    def simulate_outside(self):
        """simulats temperature change over time
        since uniform random distribution is used the expected outcome for longterm simulations will be around the initial value
        temperature  range is limited to [-15, 50]
        """
        tdelta = self.get_simulation_delta_time()
        self.value += max(-15, min(np.random.uniform(-self.change_per_minute*tdelta, self.change_per_minute*tdelta),50))
        self.lastsimulation = dt.datetime.now()



class NoiseSensor(Sensor):
    def __init__(self, location: str, init_value=50, dataService=None) -> None:
        self.type="noise"
        self.value = init_value
        self.location = location
        self.dataService = dataService
        self.lastsimulation: dt.datetime = dt.datetime.now()
        self.change_per_minute = 0.2

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
# %%
