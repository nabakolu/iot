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
  //contains all items visible in the web apps navigation sidebar
  sidebarNavItems = [
    {
      name: "Dashboard",
      material: "dashboard",
      routerLink: "/dashboard"
    },
    {
      name: "Sensors",
      material: "sensors",
      routerLink: "/sensors"
    },
    {
      name: "Actuators",
      material: "developer_board",
      routerLink: "/actuators"
    },
    {
      name: "Customize",
      material: "settings",
      routerLink: "/customize"
    },
    {
      name: "Console",
      material: "code",
      routerLink: "/console"
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
