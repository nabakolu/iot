import { Injectable } from '@angular/core';
import { io } from "socket.io-client";
import { Observable } from 'rxjs';
import * as Rx from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private socket: any;
  private subject!: Rx.Subject<any>;
  public exDataValue: number;

  constructor() {
    console.log("Data service constructor running")
    this.exDataValue = 0;
    this.connect();
    this.set_listeners();
  }

  connect(){
    console.log("connecting")
    this.socket = io('http://localhost:5000');
    this.socket.emit("log", "connected test message")
  }

  set_listeners(){
    this.socket.on('message', (data: any) => {
      console.log("Received message from Websocket Server", data)
    })
    this.socket.on('exDataValue', (data: number) => {
      console.log("Received exDataValue: ", data)
      this.exDataValue = Math.round(data*100)/100
    })
  }
}
