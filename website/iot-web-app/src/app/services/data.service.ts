import { Injectable } from '@angular/core';
import { io } from "socket.io-client";
import { Observable } from 'rxjs';
import * as Rx from 'rxjs';
import {
  MqttService
} from 'ngx-mqtt';
import { catchError, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { MatSnackBar } from '@angular/material/snack-bar';
import { UpdateStatusComponent } from '../components/snackbars/update-status/update-status.component';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private socket: any;
  private subject!: Rx.Subject<any>;
  public exDataValue: number;

  private readonly prefCoValTopic = "/CoValuePreferrence";

  constructor(private _mqttService: MqttService, private _snackBar: MatSnackBar) {
    console.log("Data service constructor running")
    this.exDataValue = 0;
    this.connect();
    this.set_listeners();
  }

  connect() {
    //websocket
    console.log("connecting")
    this.socket = io('http://localhost:5000');
    this.socket.emit("log", "connected test message")
  }

  set_listeners() {
    this.socket.on('message', (data: any) => {
      console.log("Received message from Websocket Server", data)
    })
    this.socket.on('exDataValue', (data: number) => {
      console.log("Received exDataValue: ", data)
      this.exDataValue = Math.round(data * 100) / 100
    })
  }

  publishMQTT(topic: string, message: string, retain: boolean) {
    this._mqttService.unsafePublish(topic, message, { qos: 1, retain: false });
  }

  updateCoPreferenceMQTT(value$: Observable<number>) {
    value$.pipe(
      debounceTime(800),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing co2 pref on server to:", result)
      this._mqttService.publish(this.prefCoValTopic, String(result), { qos: 1, retain: false }).subscribe(
        () => { },
        () => {
          this._snackBar.openFromComponent(UpdateStatusComponent, {
            data: {
              message: "Failed to update CO2 preferrence",
              success: false
            },
            duration: 10000,
            panelClass: ['status-snackbar']
          })
        },
        () => {
          this._snackBar.openFromComponent(UpdateStatusComponent, {
            data: {
              message: "Successfully updated CO2 preferrence",
              success: true
            },
            duration: 10000,
            panelClass: ['status-snackbar']
          })
        }
      );
    });
  }
}
