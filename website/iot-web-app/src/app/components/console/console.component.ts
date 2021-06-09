import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import {ConsoleItem} from './console-item';

@Component({
  selector: 'app-console',
  templateUrl: './console.component.html',
  styleUrls: ['./console.component.css']
})

export class ConsoleComponent implements OnInit {
  @ViewChild("areaElem") areaElem!: ElementRef;
  //two way bound to input textarea
  consoleInput: string = "";
  consoleContent: Array<ConsoleItem> = [];

  constructor() { }

  ngOnInit(): void {

  }
  ngAfterViewInit() { }


  submitConsoleInput(){
    let areaElem =  this.areaElem.nativeElement; 
    this.handleConsoleInput(this.consoleInput)
    //reset textfield by manipulating value property 
    //!!!using two way binding to reset doesn't trigger the resize function correctly --> hack with timeout
    setTimeout(function(){
      areaElem.value="";
    },0);
  }

  handleConsoleInput(input: string){
    console.log(input)
    let inptItm: ConsoleItem = new ConsoleItem(true, input);
    let inptId: string = inptItm.getId();
    this.consoleContent.push(inptItm);
    let response = this.parseConsoleCommand(input);
    if (response) {
      this.consoleContent.push(new ConsoleItem(false, response, inptId))
    }
  }

  focusInputArea(){
    this.areaElem.nativeElement.focus();
  }

  parseConsoleCommand(command: string) : string | null {
    if (command.toLowerCase().startsWith("help")) {
      return `This is the AWP commandline tool most commands are still under developement
Available commands are:
  -help
  -mqtt -[topic] -[message]`
    }
    else if (command.toLowerCase().startsWith("mqtt")){
      return "This command will be available soon"
    }
    else{
      return "Unrecognized command type 'help' to get an overview of available commands"
    }
    
  }

}
