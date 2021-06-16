#include "window.h"
#include "blinds.h"

window w;

void setup() {
	w.attach(D8);
	close_window(&w);
}

void loop() {
}
