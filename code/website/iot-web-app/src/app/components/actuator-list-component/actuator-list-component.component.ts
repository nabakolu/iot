 import { ThrowStmt } from '@angular/compiler';
import { AfterViewInit, Component, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTable } from '@angular/material/table';
import { DataService } from 'src/app/services/data.service';
import { Actuator } from 'src/app/services/sensorInterfaces';
import { ActuatorListComponentDataSource} from './actuator-list-component-datasource';

@Component({
  selector: 'app-actuator-list-component',
  templateUrl: './actuator-list-component.component.html',
  styleUrls: ['./actuator-list-component.component.css']
})
export class ActuatorListComponentComponent implements AfterViewInit {
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatTable) table!: MatTable<Actuator>;
  dataSource: ActuatorListComponentDataSource;

  /** Columns displayed in the table. Columns IDs can be added, removed, or reordered. */
  displayedColumns = ['type', 'location', 'status', 'setting'];

  constructor(public dataServiceInstance: DataService) {
    this.dataSource = new ActuatorListComponentDataSource(dataServiceInstance.actuatorList);
  }

  ngAfterViewInit(): void {
    this.initDs();
    this.onAvailActuatorsChange();
  }

  initDs(){
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
    this.table.dataSource = this.dataSource;
  }

  onAvailActuatorsChange(){
    this.dataServiceInstance.actuatorList$.subscribe((updatedList) => {
      this.dataSource = new ActuatorListComponentDataSource(updatedList);
      this.initDs();
    })
  }

}
