#include "window.c"
#include "blinds.c"

window w;

void setup() {
	w.attach(D8);
	close_window(&w);
}

void loop() {
}
