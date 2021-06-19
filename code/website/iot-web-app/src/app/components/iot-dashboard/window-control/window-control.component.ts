import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-window-control',
  templateUrl: './window-control.component.html',
  styleUrls: ['./window-control.component.css', './../iot-dashboard.component.css']
})
export class WindowControlComponent implements OnInit {
  selectedWindowModeIndex?: number = undefined;
  selectedBlindsModeIndex?: number = undefined;

  constructor() { }

  ngOnInit(): void {
  }

}