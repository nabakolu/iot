import { ChangeContext, LabelType, Options } from '@angular-slider/ngx-slider';
import { Component, OnInit } from '@angular/core';
import { Subject } from 'rxjs';
import { DataService } from 'src/app/services/data.service';

interface TempSliderModel {
  minValue: number;
  maxValue: number;
  options: Options;
}

interface coSliderModel {
  value: number;
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

  coSlider: coSliderModel = {
    value: 5,
    options: {
      showTicks: true,
      hideLimitLabels: true,
      hidePointerLabels: true,
      stepsArray: [
        {value: 1, legend: '<b>Poor</b>'},
        {value: 2, legend: '<b>Fair</b>'},
        {value: 3, legend: '<b>Average</b>'},
        {value: 4, legend: '<b>Good</b>'},
        {value: 5, legend: '<b>Excellent</b>'}
      ],
    },
  };
  coPreference$: Subject<number> = new Subject<number>();

  constructor(public dataServiceInstance: DataService) { 
    dataServiceInstance.updateCoPreferenceMQTT(this.coPreference$.asObservable());
  }

  ngOnInit(): void {  }

  onCoTargetUserChange(context: ChangeContext){
    this.coPreference$.next(context.value);
  }

}
