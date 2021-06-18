import { Component, OnInit } from '@angular/core';
import { LabelType, Options } from '@angular-slider/ngx-slider';

interface heaterIntensitySliderModel {
  value: number;
  options: Options;
}

@Component({
  selector: 'app-heating-control',
  templateUrl: './heating-control.component.html',
  styleUrls: ['./heating-control.component.css', './../iot-dashboard.component.css']
})
export class HeatingControlComponent implements OnInit {
  selectedHeatingMode: number = 0;
  heaterIntensitySlider: heaterIntensitySliderModel = {
    value: 0,
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

  constructor() { }

  ngOnInit(): void {
  }

}
