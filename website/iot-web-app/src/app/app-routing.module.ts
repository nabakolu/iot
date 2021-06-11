import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {IotDashboardComponent} from './components/iot-dashboard/iot-dashboard.component';
import {SensorListComponentComponent} from './components/sensor-list-component/sensor-list-component.component';
import {ConsoleComponent} from './components/console/console.component';
import {CustomizeComponent} from './components/customize/customize.component';

const routes: Routes = [
  { path: 'dashboard', component: IotDashboardComponent },
  { path: 'sensors', component: SensorListComponentComponent },
  { path: 'console', component: ConsoleComponent },
  { path: 'customize', component: CustomizeComponent },
  { path: '',   redirectTo: '/dashboard', pathMatch: 'full' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
