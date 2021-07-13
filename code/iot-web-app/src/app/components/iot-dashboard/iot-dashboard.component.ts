import { Component } from '@angular/core';
import { map } from 'rxjs/operators';
import { Breakpoints, BreakpointObserver } from '@angular/cdk/layout';
import { DataService } from 'src/app/services/data.service';


@Component({
  selector: 'app-iot-dashboard',
  templateUrl: './iot-dashboard.component.html',
  styleUrls: ['./iot-dashboard.component.css']
})
export class IotDashboardComponent {
  test: number = 4;
  constructor(private breakpointObserver: BreakpointObserver, public dataServiceInstance: DataService) {

  }
}
