import { LabelType, Options } from '@angular-slider/ngx-slider';
import { Component, OnInit } from '@angular/core';

interface TempSliderModel {
  minValue: number;
  maxValue: number;
  options: Options;
}


@Component({
  selector: 'app-customize',
  templateUrl: './customize.component.html',
  styleUrls: ['./customize.component.css']
})
export class CustomizeComponent implements OnInit {

  tempSlider: TempSliderModel = {
    minValue: 15,
    maxValue: 30,
    options: {
      floor: 10,
      ceil: 30,
      step: 0.1,
      translate: (value: number, label: LabelType): string => {
        switch (label) {
          case LabelType.Low:
            return '<b>Min temp:</b>&nbsp;' + value + '&#8451;';
          case LabelType.High:
            return '<b>Max temp:</b>&nbsp;' + value + '&#8451;';
          default:
            return value + "&#8451;";
        }
      }
    },
  };

  constructor() { }

  ngOnInit(): void {
  }

}
