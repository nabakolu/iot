export class ConsoleItem {
    id: string
    input: boolean
    content: string
    responseTo: string | undefined

    constructor(input: boolean, content: string, responseTo?: string) {
        this.id = this.uuidv4();
        this.input = input;
        this.content = content;
        this.responseTo = responseTo ? responseTo : undefined;
    }

    /** 
     * generate a uuidv4 string
     */
    uuidv4(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * get id of console item
     */
    getId(): string {
        return this.id;
    }

    /**
     * check if console item is a input
     */
    isInput(): boolean {
        return this.input;
    }

    /**
     * get text content of console item
     */
    getContent(): string {
        return this.content;
    }
}
