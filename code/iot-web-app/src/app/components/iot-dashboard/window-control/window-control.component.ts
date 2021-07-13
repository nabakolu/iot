import { Component, Input, OnInit } from '@angular/core';
import { MqttService } from 'ngx-mqtt';
import { Observable, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { DataService } from 'src/app/services/data.service';
import { Actuator } from 'src/app/services/sensorInterfaces';

@Component({
  selector: 'app-window-control',
  templateUrl: './window-control.component.html',
  styleUrls: ['./window-control.component.css', './../iot-dashboard.component.css']
})
export class WindowControlComponent implements OnInit {
  @Input() windowLoc!: string;


  selectedWindowModeIndex?: number = undefined;
  selectedBlindsModeIndex?: number = undefined;


  windowstate!: Actuator | undefined;

  windowmode$: Subject<string> = new Subject<string>();
  blindmode$: Subject<string> = new Subject<string>();
  constructor(public dataServiceInstance: DataService, private _mqttService: MqttService) {
    this.updateWindowModeMQTT(this.windowmode$.asObservable());
    this.updateBlindModeMQTT(this.blindmode$.asObservable());
  }

  ngOnInit(): void {
    this.windowstate = this.dataServiceInstance.actuators.get(this.windowLoc)?.get("windows")
  }

  getBlind(): Actuator | undefined{
    return this.dataServiceInstance.actuators.get(this.windowLoc)!.get("blinds")
  }

  setWindowMode(mode: string){
    this.windowstate!.setting = mode; 
    this.windowmode$.next(mode);
  }

  updateWindowModeMQTT(mode$: Observable<string>) {
    mode$.pipe(
      debounceTime(600),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing window mode for " + this.windowLoc + " on server to:", result)
      this._mqttService.publish("actuators/windows/" + this.windowLoc + "/mode", result, { qos: 1, retain: true }).subscribe(
        () => { },
        () => { this.dataServiceInstance.showUpdateSnackbar("Changing window mode failed for location: " + this.windowLoc, false) },
        () => { this.dataServiceInstance.showUpdateSnackbar("Successfully updated window mode for location '" + this.windowLoc + "' to " + result, true) }
      );
  });
  }

  updateBlindModeMQTT(mode$: Observable<string>) {
    mode$.pipe(
      debounceTime(600),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing blind mode " + this.windowLoc + " on server to:", result)
      this._mqttService.publish("actuators/blinds/" + this.windowLoc + "/mode", result, { qos: 1, retain: true }).subscribe(
        () => { },
        () => { this.dataServiceInstance.showUpdateSnackbar("Changing blind mode failed for location: " + this.windowLoc, false) },
        () => { this.dataServiceInstance.showUpdateSnackbar("Successfully updated blind mode for location '" + this.windowLoc + "' to " + result, true) }
      );
  });
  }

  setBlindMode(mode: string){
    this.getBlind()!.setting = mode; 
    this.blindmode$.next(mode);
  }

}
