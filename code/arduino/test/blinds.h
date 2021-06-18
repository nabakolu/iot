#include <Servo.h>

#define blinds Servo

void open_blinds(blinds* b){
	b->write(180);
}
void close_blinds(blinds* b){
	b->write(0);
}
