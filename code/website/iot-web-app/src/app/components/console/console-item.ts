export class ConsoleItem {
    id: string
    input: boolean
    content: string
    responseTo: string | undefined

    constructor(input: boolean, content: string, responseTo?: string){
        this.id = this.uuidv4();
        this.input = input;
        this.content = content;
        this.responseTo = responseTo ? responseTo : undefined;
    }

    uuidv4(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    getId(){
        return this.id;
    }

    isInput(){
        return this.input;
    }

    getContent(){
        return this.content;
    }
}
