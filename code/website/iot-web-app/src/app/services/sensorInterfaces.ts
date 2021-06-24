export interface Actuator {
    type: string,
    location: string,
    status: string | null | number,
    setting: string
}

export interface Heater extends Actuator{
    status: number,
    //when heating is set to manual
    power: number;
}

export interface Sensor{
    //what kind of sensor is it?
    type: string;
    location: string;
    value: any;
}

export interface StatusUpdate {
    actuatorType: string;
    location: string;
    msg: string;
}