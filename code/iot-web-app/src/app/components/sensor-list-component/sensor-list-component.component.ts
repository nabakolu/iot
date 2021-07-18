import { AfterViewInit, Component, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTable } from '@angular/material/table';
import { DataService } from 'src/app/services/data.service';
import { Sensor } from 'src/app/services/sensorInterfaces';
import { SensorListComponentDataSource} from './sensor-list-component-datasource';

@Component({
  selector: 'app-sensor-list-component',
  templateUrl: './sensor-list-component.component.html',
  styleUrls: ['./sensor-list-component.component.css']
})
export class SensorListComponentComponent implements AfterViewInit {
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;
  @ViewChild(MatTable) table!: MatTable<Sensor>;
  dataSource: SensorListComponentDataSource;

  /** Columns displayed in the table. Columns IDs can be added, removed, or reordered. */
  displayedColumns = ['type', 'location', 'value'];

  constructor(public dataServiceInstance: DataService) {
    this.dataSource = new SensorListComponentDataSource(dataServiceInstance.sensorList);
  }

  ngAfterViewInit(): void {
    this.initDs();
    this.onAvailSensorsChange();
  }

  initDs(){
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
    this.table.dataSource = this.dataSource;
  }

  onAvailSensorsChange() {
    //wait for changes then update underlying data
    this.dataServiceInstance.sensorList$.subscribe((updatedList) => {
      this.dataSource = new SensorListComponentDataSource(updatedList);
      this.initDs();
    })
  }
}
