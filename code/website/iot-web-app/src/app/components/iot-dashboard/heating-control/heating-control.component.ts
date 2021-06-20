import { Component, OnInit } from '@angular/core';
import { ChangeContext, LabelType, Options } from '@angular-slider/ngx-slider';
import { MqttService } from 'ngx-mqtt';
import { DataService } from 'src/app/services/data.service';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { Observable, Subject } from 'rxjs';

interface heaterIntensitySliderModel {
  options: Options;
}

@Component({
  selector: 'app-heating-control',
  templateUrl: './heating-control.component.html',
  styleUrls: ['./heating-control.component.css', './../iot-dashboard.component.css']
})
export class HeatingControlComponent implements OnInit {
  heaterIntensitySlider: heaterIntensitySliderModel = {
    options: {
      step: 0.1,
      floor: 0,
      ceil: 100,
      translate: (value: number, label: LabelType): string => {
        switch(value) {
          case 0:
            return "OFF";
          default:
            return value + "&#37;";
        }
      }
    }  
  }

  heatermode$: Subject<string> = new Subject<string>();
  heaterpower$: Subject<number> = new Subject<number>();

  constructor(public dataServiceInstance: DataService, private _mqttService: MqttService) {
    this.updateHeaterModeMQTT(this.heatermode$.asObservable());
    this.updateHeaterPowerMQTT(this.heaterpower$.asObservable());
  }

  ngOnInit(): void {
  }

  setHeatingMode(mode: string){
    this.dataServiceInstance.heater.setting = mode; 
    this.heatermode$.next(mode);
  }

  onPowerSliderChange(context: ChangeContext){
    this.heaterpower$.next(context.value);
  }

  updateHeaterModeMQTT(mode$: Observable<string>) {
    mode$.pipe(
      debounceTime(600),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing window mode for heater on server to:", result)
      this._mqttService.publish("/actuators/heating/mode", result, { qos: 1, retain: true }).subscribe(
        () => { },
        () => { this.dataServiceInstance.showUpdateSnackbar("Failed to change heating mode to: " + result, false) },
        () => { this.dataServiceInstance.showUpdateSnackbar("Successfully updated heating mode to " + result, true) }
      );
  });
  }

  updateHeaterPowerMQTT(mode$: Observable<number>) {
    mode$.pipe(
      debounceTime(600),
      distinctUntilChanged()
    ).subscribe(result => {
      console.log("changing window mode for heater on server to:", result)
      this._mqttService.publish("/actuators/heating/power", String(result), { qos: 1, retain: true }).subscribe(
        () => { },
        () => { this.dataServiceInstance.showUpdateSnackbar("Failed to change heating mode to: " + result, false) },
        () => { this.dataServiceInstance.showUpdateSnackbar("Successfully updated heating power to " + result + "% power", true) }
      );
  });
  }

}
