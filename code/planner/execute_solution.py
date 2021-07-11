import re
import paho.mqtt.client as mqtt

def execute_solution (solution: str, client: mqtt.Client):
    """ parse output of planner and send respective mqtt messages """
    solution = solution.split(";;;; Solution Found")[1] # first get only the last part, in which the solution is listed
    solution = solution.split("\n") # split each line
    print("Executing commands:")
    for i in range(4, len(solution) - 1): # start at line 4, since there are 4 more lines with useless information, until the actual solutions starts
        command, location = re.findall(r"\((.*?)\)", solution[i])[0].split(' ', 1) # split content inside bracktes into command and location
        location = location.split('_', 1)[1] # transform lacation into real location e.g. window_east -> east
        print(command + " :: " + location)

        # depending on command send appropriate mqtt message
        if command == "openwindow":
            client.publish("actuators/windows/" + location + "/command", "open")

        if command == "closewindow":
            client.publish("actuators/windows/" + location + "/command", "close")

        if command == "openblinds":
            client.publish("actuators/blinds/" + location + "/command", "open")

        if command == "closeblinds":
            client.publish("actuators/blinds/" + location + "/command", "close")

        if command == "turn_heater_on":
            client.publish("actuators/heating/command", "100")

        if command == "turn_heater_off":
            client.publish("actuators/heating/command", "0")
