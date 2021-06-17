import { Injectable } from '@angular/core';
import { io } from "socket.io-client";
import { BehaviorSubject, Observable } from 'rxjs';
import * as Rx from 'rxjs';
import {
  MqttService
} from 'ngx-mqtt';
import { catchError, debounceTime, distinctUntilChanged, filter, map } from 'rxjs/operators';
import { MatSnackBar } from '@angular/material/snack-bar';
import { UpdateStatusComponent } from '../components/snackbars/update-status/update-status.component';
import { Subject } from 'rxjs';

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

  private readonly prefCoValTopic = "CoValuePreference";
  private readonly prefTempValTopic = "TempValuePreference";
  private readonly ambientNoiseThTopic = "ambientNPreference";
  private readonly lightSenseTopic = "lightSensePreference";

  constructor(private _mqttService: MqttService, private _snackBar: MatSnackBar) {
    console.log("Data service constructor running")
    this.setup_mqtt_observers()
  }

  setup_mqtt_observers(){
    //customize component
    this.setupCoObserver();
    this.setupTempObserver();
    this.setupAmbientNoiseObserver();
    this.setupLightSenseObserver();
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
      distinctUntilChanged()
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
