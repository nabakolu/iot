#include <Servo.h>

#define window Servo

void open_window(window* w){
	w->write(180);
}
void close_window(window* w){
	w->write(0);
}
