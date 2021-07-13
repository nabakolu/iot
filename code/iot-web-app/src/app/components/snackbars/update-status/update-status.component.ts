import { Component, Inject, OnInit } from '@angular/core';
import { MatSnackBarRef, MAT_SNACK_BAR_DATA } from '@angular/material/snack-bar';

@Component({
  selector: 'app-update-status',
  templateUrl: './update-status.component.html',
  styleUrls: ['./update-status.component.css']
})
export class UpdateStatusComponent implements OnInit {

  constructor(public snackBarRef: MatSnackBarRef<any>,@Inject(MAT_SNACK_BAR_DATA) public data: any) { 
    
  }

  ngOnInit(): void {
  }

}
