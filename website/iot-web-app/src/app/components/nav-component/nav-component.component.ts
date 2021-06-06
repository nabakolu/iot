import { Component } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';

@Component({
  selector: 'app-nav-component',
  templateUrl: './nav-component.component.html',
  styleUrls: ['./nav-component.component.css']
})
export class NavComponentComponent {

  backgroundImage = "src\assets\images\sidebar-background/cracks.jpg"
  selectedItemIndex: number;

  sidebarNavItems = [
    {
      name: "Dashboard",
      material: "dashboard",
      routerLink: "/dashboard"
    },
    {
      name: "Sensors",
      material: "developer_board",
      routerLink: "/sensors"
    },
    {
      name: "Actuators",
      material: "sensors",
      routerLink: "/sensors"
    },
    {
      name: "Customize",
      material: "settings",
      routerLink: "/sensors"
    },
    {
      name: "Console",
      material: "code",
      routerLink: "/dashboard"
    }
  ]

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(private breakpointObserver: BreakpointObserver) {
    this.selectedItemIndex = 0;
  }
}
