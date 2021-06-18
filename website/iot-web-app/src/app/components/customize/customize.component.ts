import { ChangeContext, LabelType, Options } from '@angular-slider/ngx-slider';
import { Component, OnInit } from '@angular/core';
import { Subject, Subscription } from 'rxjs';
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
  selectedAmbientNoiseValue?: string;
  selectedLightSenseValue?: string;

  coPreference$: Subject<number> = new Subject<number>();
  tempPreference$: Subject<any> = new Subject<Array<number>>();
  ambientNoisePref$: Subject<any> = new Subject<string>();
  lightSensPref$: Subject<any> = new Subject<string>();

  subscriptions: Array<Subscription> = [];  


  constructor(public dataServiceInstance: DataService) { 
    //---- CO2
    //change from client
    this.subscriptions.push(dataServiceInstance.updateCoPreferenceMQTT(this.coPreference$.asObservable()));
    //change from server
    this.subscriptions.push(this.dataServiceInstance.coPreference$.subscribe(this.onCoTargetServerChange.bind(this)));
    //---- CO2
    //change from client
    this.subscriptions.push(dataServiceInstance.updateTempPreferenceMQTT(this.tempPreference$.asObservable()));
    //change from server
    this.subscriptions.push(this.dataServiceInstance.tempPreference$.subscribe(this.onTempTargetServerChange.bind(this)));
    //---- Ambient Noise
    //change from client
    this.subscriptions.push(dataServiceInstance.updateAmbientNoisePreferenceMQTT(this.ambientNoisePref$.asObservable()));
    //change from server
    this.subscriptions.push(this.dataServiceInstance.ambientNoisePref$.subscribe(this.onAmbientNoiseServerChange.bind(this)));
    //---- Light Sensitivity
    //change from client
    this.subscriptions.push(dataServiceInstance.updateLightSensePreferenceMQTT(this.lightSensPref$.asObservable()));
    //change from server
    this.subscriptions.push(this.dataServiceInstance.lightSensPref$.subscribe(this.onLightSensServerChange.bind(this)));
  }

  ngOnInit(): void {  }

  ngOnDestroy() {
    //unsubscribe all subscriptions of this component
    for(let i=0; i<this.subscriptions.length; i++){
      this.subscriptions[i].unsubscribe();
    }
  }

  onCoTargetUserChange(context: ChangeContext){
    this.coPreference$.next(context.value);
  }

  onCoTargetServerChange(message: any){
    this.coSlider.value = message;
  }

  setCoToDefault(){
    this.coPreference$.next(4);
    this.coSlider.value = 4;
  }

  onTempTargetUserChange(context: ChangeContext){
    this.tempPreference$.next([context.value, context.highValue]);
  }

  onTempTargetServerChange(message: any){
    console.log("message temp arr")
    this.tempSlider.minValue = message[0];
    this.tempSlider.maxValue = message[1];
  }

  setTempTargetToDefault(){
    this.tempPreference$.next([17, 23]);
    this.tempSlider.minValue = 17;
    this.tempSlider.maxValue = 23;
  }

  onAmbientNoiseUserChange(changeEv: any){
    this.ambientNoisePref$.next(changeEv.value);
  }

  onAmbientNoiseServerChange(message: string){
    this.selectedAmbientNoiseValue = message;
  }

  setAmbientNoiseToDefault(){
    this.ambientNoisePref$.next("mid");
    this.selectedAmbientNoiseValue = "mid";
  }

  onLightSensUserChange(changeEv: any){
    this.lightSensPref$.next(changeEv.value);
  }

  onLightSensServerChange(message: string){
    this.selectedLightSenseValue = message;
  }

  setLightSenseToDefault(){
    this.lightSensPref$.next("mid");
    this.selectedLightSenseValue = "mid";
  }

}
