import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {IotDashboardComponent} from './iot-dashboard/iot-dashboard.component';
import {SensorListComponentComponent} from './sensor-list-component/sensor-list-component.component';

const routes: Routes = [
  { path: 'dashboard', component: IotDashboardComponent },
  { path: 'sensors', component: SensorListComponentComponent },
  { path: '',   redirectTo: '/dashboard', pathMatch: 'full' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
