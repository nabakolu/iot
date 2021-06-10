import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { DataService } from 'src/app/services/data.service';
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
  commandMemory: Array<string> = [""];
  indexInMemory: number = 0;

  constructor(private dataServiceInstance: DataService) { }

  ngOnInit(): void {

  }
  ngAfterViewInit() { }


  submitConsoleInput(){
    let areaElem =  this.areaElem.nativeElement; 
    this.commandMemory.splice(1, 0, this.consoleInput)
    this.indexInMemory = 0;
    this.commandMemory[0] = "";
    this.handleConsoleInput(this.consoleInput)
    //reset textfield by manipulating value property 
    //!!!using two way binding to reset doesn't trigger the resize function correctly --> hack with timeout
    setTimeout(function(){
      areaElem.value="";
    },0);
    this.consoleInput = "";
  }

  consoleArrowNavigation(direction: string){
    let comp = this;
    console.warn("im working:", direction, ":::", this.indexInMemory)
    console.warn(this.commandMemory)
    if (direction === "up"){
      if (this.commandMemory.length > this.indexInMemory+1){
        this.commandMemory[this.indexInMemory] = this.consoleInput == "\n"? "": this.consoleInput;
        this.indexInMemory++;
        this.consoleInput = "";
        setTimeout(function(){
          comp.areaElem.nativeElement.value="";
        },0);
        this.consoleInput = comp.commandMemory[comp.indexInMemory];
        setTimeout(function(){
          comp.areaElem.nativeElement.value=comp.commandMemory[comp.indexInMemory];
        },0);
      }
    }
    else if (this.indexInMemory>0){
      this.commandMemory[this.indexInMemory] = this.consoleInput == "\n"? "": this.consoleInput;
      this.indexInMemory--;
      this.consoleInput = "";
      setTimeout(function(){
        comp.areaElem.nativeElement.value="";
      },0);
      this.consoleInput = comp.commandMemory[comp.indexInMemory];
      setTimeout(function(){
        comp.areaElem.nativeElement.value=comp.commandMemory[comp.indexInMemory];
      },0);
    }
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
      let cmdParts: Array<string> = command.split("--")
      let topic: string = cmdParts[1]
      let message: string = cmdParts[2]
      this.dataServiceInstance.publishMQTT(topic, message, false);
      return "Send MQTT message to topic: " + topic
    }
    else{
      return "Unrecognized command type 'help' to get an overview of available commands"
    }
    
  }

}
