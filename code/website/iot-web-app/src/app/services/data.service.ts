import { Injectable } from '@angular/core';
import { io } from "socket.io-client";
import { BehaviorSubject, Observable, of } from 'rxjs';
import * as Rx from 'rxjs';
import {
  IMqttMessage,
  MqttService
} from 'ngx-mqtt';
import { catchError, concatMap, debounceTime, distinctUntilChanged, filter, map, observeOn, tap } from 'rxjs/operators';
import { MatSnackBar } from '@angular/material/snack-bar';
import { UpdateStatusComponent } from '../components/snackbars/update-status/update-status.component';
import { Subject } from 'rxjs';
import {Window, Heater, Sensor, StatusUpdate, Actuator} from './sensorInterfaces';
import { queueScheduler } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private socket: any;
  private dataServiceId: string = this.uuidv4();
  //observers for customize component
  public coPreference$: BehaviorSubject<any> = new BehaviorSubject<any>(4);
  public tempPreference$: BehaviorSubject<any> = new BehaviorSubject<any>([17, 23]);
  public ambientNoisePref$: BehaviorSubject<any> = new BehaviorSubject<any>("mid");
  public lightSensPref$: BehaviorSubject<any> = new BehaviorSubject<any>("mid");

  //subject to process actuator messages synchronously
  private actuatorQueue = new Subject<IMqttMessage>();
  //subject to process actuator messages synchronously
  private sensorQueue = new Subject<IMqttMessage>();

  //mqtt topics for customize component
  private readonly prefCoValTopic = "CoValuePreference";
  private readonly prefTempValTopic = "TempValuePreference";
  private readonly ambientNoiseThTopic = "ambientNPreference";
  private readonly lightSenseTopic = "lightSensePreference";
  //mqtt topic for actuators (windows, blind)
  private readonly actuatorTopic = "actuators/+/+/+";
  private readonly heatingTopic = "actuators/+/+";
  //mqtt topic for sensors --> display in list with connected sensors
  private readonly sensorTopic = "sensors/#";

  //connected actuators (windows, blinds)
  public actuators: Map<string, Map<string, Actuator>> = new Map();
  //connected heater
  public heater: Heater = {type: "heater", location: "CentralHeatingElem", status: 0, setting: "auto", power: 0};
  public insideTemp?: number = undefined;
  public outsideTemp?: number = undefined;
  //all connected actuators as list to display in actuator tab as list
  public actuatorList: Array<Actuator> = [];
  public actuatorList$: BehaviorSubject<Array<Actuator>> = new BehaviorSubject<Array<Actuator>>([]);
  //sensors
  public sensors: Map<String, Sensor> = new Map();
  public sensorList: Array<Sensor> = [];
  public sensorList$: BehaviorSubject<Array<Sensor>> = new BehaviorSubject<Array<Sensor>>([]);

  constructor(private _mqttService: MqttService, private _snackBar: MatSnackBar) {
    console.log("Data service constructor running")
    this.processActuatorMessages();
    this.processSensorMessages();
    this.setup_mqtt_observers();
  }

  setup_mqtt_observers(){
    //customize component
    this.setupCoObserver();
    this.setupTempObserver();
    this.setupAmbientNoiseObserver();
    this.setupLightSenseObserver();
    //dashboard component + actuator list component
    this.setupActuators();
    //sensor list component + temperature information
    this.setupSensors();
  }

  setupSensors(){
    this._mqttService.observe(this.sensorTopic).subscribe(msg => {
      this.sensorQueue.next(msg);
    })
  }

  setupActuators(){
    this._mqttService.observe(this.actuatorTopic).subscribe(msg => {
      this.actuatorQueue.next(msg);
    });
    this._mqttService.observe(this.heatingTopic).subscribe(msg => {
      this.actuatorQueue.next(msg);
    });
  }

  processSensorMessages(){
    this.sensorQueue.pipe(concatMap(msg => of(msg))).subscribe((msg) => {
      let topicParts = msg.topic.split("/");
      let sensorType: string = topicParts[1], location: string = topicParts[2]
      if(sensorType == "temperature"){
        if(location == "inside"){
          this.insideTemp = Number(msg.payload.toString());
        }
        if(location == "outside"){
          this.outsideTemp = Number(msg.payload.toString());
        }
      }
      let sensor: Sensor = {location: location, type: sensorType, value: msg.payload.toString()};
      this.sensors.set(JSON.stringify([location, sensorType]), sensor);
      this.updateSensorList();
    });
  }

  updateSensorList(){
    let tempSensList: Array<Sensor> = [];
    //get all actuators (windows, blinds)
    this.sensors.forEach((sensor, key) => {
      tempSensList.push(sensor)
    });
    this.sensorList.length = 0;
    Array.prototype.push.apply(this.sensorList, tempSensList);
    this.sensorList$.next(tempSensList);
  }

  processActuatorMessages(){
    this.actuatorQueue.pipe(concatMap(msg => of(msg))).subscribe((msg) => {
      let topicParts = msg.topic.split("/");
      let actuatorType: string = topicParts[1], location: string = topicParts[2], msgType: string=topicParts[3];
      //for heaters
      if(actuatorType=="heating"){
        switch(location){
          case "status":
            this.heater.status = Number(msg.payload.toString())
            break;
          case "command":
            console.log("command message arr")
            break;
          case "mode":
            this.heater.setting = msg.payload.toString();
            break;
          case "power":
            this.heater.power = Number(msg.payload.toString())
            break;
          default:
            console.warn("Actuator heating message with unknown topic arrived: ", msgType)
        }
      }
      //other actuators
      else{
        this.updateActuators(location, actuatorType);
        let statusUpdate: StatusUpdate = {actuatorType: actuatorType, location: location, msg: msg.payload.toString()};
        switch(msgType){
          case "status":
            this.processActuatorStatusUpdates(statusUpdate);
            break;
          case "command":
            console.log("command message arr")
            break;
          case "mode":
            console.log("mode message arr")
            this.processModeUpdates(statusUpdate);
            break;
          default:
            console.warn("Actuator message with unknown topic arrived: ", msgType)
        }
      }
      this.updateActuatorList();
    });
  }

  processModeUpdates(statusUpdate: StatusUpdate){
    this.actuators.get(statusUpdate.location)!.get(statusUpdate.actuatorType)!.setting = statusUpdate.msg;
  }

  updateActuators(location: string, type: string){
    //check if location already exists if not add location
    if(!this.actuators.has(location)){
      this.actuators.set(location, new Map());
    }
    //check if sensor type for location already exists if not add sensor type
    if(!this.actuators.get(location)!.has(type)){
      let actuator: Actuator = {type: type, location: location, setting: "auto", status: null}
      this.actuators.get(location)?.set(type, actuator)
    }
  }

  updateActuatorList(){
    let tempActList: Actuator[] = [];
    //get all actuators (windows, blinds)
    this.actuators.forEach((actTypeMap, location) => {
        actTypeMap.forEach((actuator, type) =>
        {
          tempActList.push(actuator);
        })
    })
    tempActList.push(this.heater);
    this.actuatorList.length = 0;
    Array.prototype.push.apply(this.actuatorList, tempActList);
    this.actuatorList$.next(tempActList);
  }

  setupCoObserver(){
    //co2 preferences
    this._mqttService.observe(this.prefCoValTopic).pipe(map(message => JSON.parse(message.payload.toString())),
    filter(message => message.id !== this.dataServiceId),
    map(message => message.data)
    ).subscribe(this.coPreference$)
  }

  setupTempObserver(){
    //temp preferences
    this._mqttService.observe(this.prefTempValTopic).pipe(map(message => JSON.parse(message.payload.toString())),
    filter(message => message.id !== this.dataServiceId),
    map(message => message.data)
    ).subscribe(this.tempPreference$)
  }

  setupAmbientNoiseObserver(){
    //ambient noise preferences
    this._mqttService.observe(this.ambientNoiseThTopic).pipe(map(message => JSON.parse(message.payload.toString())),
    // filter(message => message.id !== this.dataServiceId),
    map(message => message.data)
    ).subscribe(this.ambientNoisePref$)
  }

  setupLightSenseObserver(){
    //ambient noise preferences
    this._mqttService.observe(this.lightSenseTopic).pipe(map(message => JSON.parse(message.payload.toString())),
    // filter(message => message.id !== this.dataServiceId),
    map(message => message.data)
    ).subscribe(this.lightSensPref$)
  }

  connect() {
    //websocket
    // console.log("connecting")
    // this.socket = io('http://localhost:5000');
    // this.socket.emit("log", "connected test message")
  }

  set_listeners() {
    // this.socket.on('message', (data: any) => {
    //   console.log("Received message from Websocket Server", data)
    // })
    // this.socket.on('exDataValue', (data: number) => {
    //   console.log("Received exDataValue: ", data)
    //   this.exDataValue = Math.round(data * 100) / 100
    // })
  }

  processActuatorStatusUpdates(statusUpdate: StatusUpdate){
    this.actuators.get(statusUpdate.location)!.get(statusUpdate.actuatorType)!.status = statusUpdate.msg;
  }

  publishMQTT(topic: string, message: string, retain: boolean) {
    this._mqttService.unsafePublish(topic, message, { qos: 1, retain: false });
  }

  updateCoPreferenceMQTT(value$: Observable<number>) {
    return value$.pipe(
      debounceTime(800),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing co2 pref on server to:", result)
      this._mqttService.publish(this.prefCoValTopic, JSON.stringify({data: result, id: this.dataServiceId}), { qos: 1, retain: true }).subscribe(
        () => { },
        () => {this.showUpdateSnackbar("Failed to update CO2 preference", false)},
        () => {this.showUpdateSnackbar("Successfully updated CO2 preference", true)}
      );
    });
  }

  updateTempPreferenceMQTT(value$: Observable<Array<number>>) {
    return value$.pipe(
      debounceTime(800),
      distinctUntilChanged((prev, curr) => prev[0] === curr[0] && prev[1] === curr[1])
    ).subscribe(result => {
      console.log("changing temp pref on server to:", result)
      this._mqttService.publish(this.prefTempValTopic, JSON.stringify({data: result, id: this.dataServiceId}), { qos: 1, retain: true }).subscribe(
        () => { },
        () => {this.showUpdateSnackbar("Failed to update Temperature preference", false)},
        () => {this.showUpdateSnackbar("Successfully updated Temperature preference", true)}
      );
    });
  }

  updateAmbientNoisePreferenceMQTT(value$: Observable<Array<number>>) {
    return value$.pipe(
      debounceTime(800),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing noise pref on server to:", result)
      this._mqttService.publish(this.ambientNoiseThTopic, JSON.stringify({data: result, id: this.dataServiceId}), { qos: 1, retain: true }).subscribe(
        () => { },
        () => {this.showUpdateSnackbar("Failed to update ambient noise preference", false)},
        () => {this.showUpdateSnackbar("Successfully updated ambient noise preference", true)}
      );
    });
  }

  updateLightSensePreferenceMQTT(value$: Observable<Array<number>>) {
    return value$.pipe(
      debounceTime(800),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing light sense pref on server to:", result)
      this._mqttService.publish(this.lightSenseTopic, JSON.stringify({data: result, id: this.dataServiceId}), { qos: 1, retain: true }).subscribe(
        () => { },
        () => {this.showUpdateSnackbar("Failed to update light sensitivity preference", false)},
        () => {this.showUpdateSnackbar("Successfully updated light sensitivity preference", true)}
      );
    });
  }

  showUpdateSnackbar(message: string, success: boolean){
    this._snackBar.openFromComponent(UpdateStatusComponent, {
      data: {
        message: message,
        success: success
      },
      duration: 10000,
      panelClass: ['status-snackbar']
    })
  }

  uuidv4(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
}
