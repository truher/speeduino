void initializeClient() {
    Serial3.begin(1000000);  // 1Mbaud, simulator can do this (and reality can too)
    Serial3.setTimeout(100); // 5ms timeout; ignitions are 5ms apart, try to make this smaller

}

void getPW() {

}
