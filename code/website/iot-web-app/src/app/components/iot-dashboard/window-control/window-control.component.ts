import { Component, Input, OnInit } from '@angular/core';
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
  constructor(public dataServiceInstance: DataService) {

  }

  ngOnInit(): void {
    // console.warn(this.dataServiceInstance.actuators)
    // console.warn(this.dataServiceInstance.actuators.get(this.windowLoc))
    console.error(this.windowLoc)
    console.error(this.dataServiceInstance.actuators.get(this.windowLoc))
    console.error(this.dataServiceInstance.actuators.get(this.windowLoc)?.get("windows"))
    this.windowstate = this.dataServiceInstance.actuators.get(this.windowLoc)?.get("windows")
    // console.warn(this.dataServiceInstance.actuators.get(this.windowLoc)!.get("windows")!)
    // this.windowstat = this.dataServiceInstance.actuators.get(this.windowLoc)!.get("windows")!
    // console.warn("got winsat", this.windowstat)
  }

}
