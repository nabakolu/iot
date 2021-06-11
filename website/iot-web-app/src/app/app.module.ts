import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
//sidebar
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatListModule} from '@angular/material/list';
import { LayoutModule } from '@angular/cdk/layout';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { NavComponentComponent } from './components/nav-component/nav-component.component';
import { IotDashboardComponent } from './components/iot-dashboard/iot-dashboard.component';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatCardModule } from '@angular/material/card';
import { MatMenuModule } from '@angular/material/menu';
import { SensorListComponentComponent } from './components/sensor-list-component/sensor-list-component.component';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { FormsModule } from '@angular/forms';
import { DataService } from './services/data.service';
import { ConsoleComponent } from './components/console/console.component';
import { TextFieldModule } from '@angular/cdk/text-field';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { NgScrollbarModule } from 'ngx-scrollbar';
import {
  IMqttMessage,
  MqttModule,
  IMqttServiceOptions
} from 'ngx-mqtt';
import { CustomizeComponent } from './components/customize/customize.component';
import { NgxSliderModule } from '@angular-slider/ngx-slider';
import {MatButtonToggleModule} from '@angular/material/button-toggle';

export const MQTT_SERVICE_OPTIONS: IMqttServiceOptions = {
  hostname: '82.165.70.137',
  port: 4005,
  path: '/mqtt',
  username: 'iotproject', 
  password: 'iotaccesspw%'
};

@NgModule({
  declarations: [
    AppComponent,
    NavComponentComponent,
    IotDashboardComponent,
    SensorListComponentComponent,
    ConsoleComponent,
    CustomizeComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    LayoutModule,
    MatButtonModule,
    MatIconModule,
    MatGridListModule,
    MatCardModule,
    MatMenuModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    TextFieldModule,
    FormsModule,
    ScrollingModule,
    NgScrollbarModule,
    MqttModule.forRoot(MQTT_SERVICE_OPTIONS),
    NgxSliderModule,
    MatButtonToggleModule,
  ],
  providers: [DataService],
  bootstrap: [AppComponent]
})
export class AppModule { }
