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
    this.commandMemory.splice(1, 0, this.consoleInput)
    this.indexInMemory = 0;
    this.commandMemory[0] = "";
    this.handleConsoleInput(this.consoleInput)
    this.clearConsole();    
  }

  consoleArrowNavigation(direction: string){
    let comp = this;
    if (direction === "up"){
      if (this.commandMemory.length > this.indexInMemory+1){
        this.commandMemory[this.indexInMemory] = this.consoleInput == "\n"? "": this.consoleInput;
        this.indexInMemory++;
        this.clearConsole();
        this.consoleInput = comp.commandMemory[comp.indexInMemory];
        setTimeout(function(){
          comp.areaElem.nativeElement.value=comp.commandMemory[comp.indexInMemory];
        },0);
      }
    }
    else if (this.indexInMemory>0){
      this.commandMemory[this.indexInMemory] = this.consoleInput == "\n"? "": this.consoleInput;
      this.indexInMemory--;
      this.clearConsole();
      this.consoleInput = comp.commandMemory[comp.indexInMemory];
      setTimeout(function(){
        comp.areaElem.nativeElement.value=comp.commandMemory[comp.indexInMemory];
      },0);
    }
  }

  clearConsole(){
    //reset textfield by manipulating value property 
    //!!!using two way binding to reset doesn't trigger the resize function correctly --> hack with timeout
    let areaElem =  this.areaElem.nativeElement; 
    this.consoleInput = "";
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
  -mqtt -[topic] -[message]
      example: mqtt -test
  -mockwindow -[location]
      example: mockwindow -north_lower
  -mockwinblin -[location]
      example mockwinblin -north-lower
  -changewindow -[location] -[change] -[msg]
      example: changewindow -north_lower -status -open
  -changeblind -[location] -[change] -[msg]
      example: changeblind -north_lower -status -open
  -mocksensor -[sensorType] -[location] -[value]
      example: mocksensor -temperature -north_lower -45.3
  -removelocation -[location]
      desc: removes all actuators connected to a location (actuators will be automatically added again if new message comes in)
      example: removelocation -north_lower
  -removesensor -[sensorType] -[location]
      example: reomvesensor -sun -east 
  `
    }
    else if (command.toLowerCase().startsWith("mqtt")){
      let cmdParts: Array<string> = command.split("-")
      let topic: string = cmdParts[1].trim()
      let message: string = cmdParts[2].trim()
      this.dataServiceInstance.publishMQTT(topic, message, true);
      return "Send MQTT message to topic: " + topic
    }
    else if (command.toLowerCase().startsWith("mockwinblin")){
      let cmdParts: Array<string> = command.split("-")
      let location: string = cmdParts[1].trim()
      this.dataServiceInstance.publishMQTT("actuators/windows/" + location + "/status", " ", true);
      this.dataServiceInstance.publishMQTT("actuators/blinds/" + location + "/status", " ", true);
      return "Created temporary blank window and blind with location: " + location
    }
    else if (command.toLowerCase().startsWith("mockwindow")){
      let cmdParts: Array<string> = command.split("-")
      let location: string = cmdParts[1].trim()
      this.dataServiceInstance.publishMQTT("actuators/windows/" + location +"/mock", " ", true);
      return "Created temporary blank window with location: " + location
    }
    else if (command.toLowerCase().startsWith("mockheating")){
      let cmdParts: Array<string> = command.split("-")
      let location: string = cmdParts[1].trim()
      this.dataServiceInstance.publishMQTT("actuators/heating/" + location +"/mock", " ", true);
      return "Created temporary blank window with location: " + location
    }
    else if (command.toLowerCase().startsWith("changewindow")){
      let cmdParts: Array<string> = command.split("-")
      let location: string = cmdParts[1].trim()
      let change: string = cmdParts[2].trim()
      let msg: string = cmdParts[3].trim()
      this.dataServiceInstance.publishMQTT("actuators/windows/" +location +"/" + change, msg, true);
      return "Change applied for window with location: " + location
    }
    else if (command.toLowerCase().startsWith("mocksensor")){
      let cmdParts: Array<string> = command.split("-")
      let sensortype: string = cmdParts[1].trim()
      let location: string = cmdParts[2].trim()
      let msg: string = cmdParts[3].trim()
      this.dataServiceInstance.publishMQTT("sensors/" + sensortype + "/" + location, msg, false);
      return "Mocked sensor with message: " + "/sensors/" + sensortype + "/" + location
    }
    else if (command.toLowerCase().startsWith("changeblind")){
      let cmdParts: Array<string> = command.split("-")
      let location: string = cmdParts[1].trim()
      let change: string = cmdParts[2].trim()
      let msg: string = cmdParts[3].trim()
      this.dataServiceInstance.publishMQTT("actuators/blinds/" +location +"/" + change, msg, true);
      return "Change applied for blind with location: " + location
    }
    else if (command.toLowerCase().startsWith("removelocation")){
      let cmdParts: Array<string> = command.split("-")
      let location: string = cmdParts[1].trim()
      this.dataServiceInstance.publishMQTT("actuators/blinds/" +location +"/status", "", true);
      this.dataServiceInstance.publishMQTT("actuators/blinds/" +location +"/mode", "", true);
      this.dataServiceInstance.publishMQTT("actuators/windows/" +location +"/status", "", true);
      this.dataServiceInstance.publishMQTT("actuators/windows/" +location +"/mode", "", true);
      this.dataServiceInstance.publishMQTT("actuators/windows/" +location +"/mock", "", true);
      this.dataServiceInstance.publishMQTT("actuators/blinds/" +location +"/mock", "", true);
      return "Deleted all actuators for location: " + location
    }
    else if (command.toLowerCase().startsWith("removesensor")) {
      let cmdParts: Array<string> = command.split("-")
      let type: string = cmdParts[1].trim()
      let location: string = cmdParts[2].trim()
      this.dataServiceInstance.publishMQTT("sensors/" + type + "/" + location + "/status", "", true);
      return "Deleted sensor of type: " + type + " at location: " + location
    }
    else{
      return "Unrecognized command type 'help' to get an overview of available commands"
    }
    
  }

}
