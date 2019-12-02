/* Working out ADC pins */

#define BIT_SET(a,b) ((a) |= (1U<<(b)))
#define BIT_CLEAR(a,b) ((a) &= ~(1U<<(b)))

//volatile int pin;
volatile byte loopCounter;
volatile int val[16] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};

void setup() {
  //pin = PF1;
  //pin = A0;  // A0 in arduino-land means "analog pin 0"
  // and indeed you can use values like A12, and not values like K2
  // but there is unfortunately also a pin called A0 like PA0.
  // is simulavr using those?
  loopCounter = 0;
  //val = 0;
  // ADCSRA = adc control and status register a
  // ADPS = prescaler select
  // 100 = divide by 16
  // https://sites.google.com/site/qeewiki/books/avr-guide/analog-input
  BIT_SET(ADCSRA,ADPS2);
  BIT_CLEAR(ADCSRA,ADPS1);
  BIT_CLEAR(ADCSRA,ADPS0);
}

void loop() {
  loopCounter += 1;
  //val[0] = analogRead(0);
  //val[1] = analogRead(1);
  val[0] = analogRead(A0);
  val[1] = analogRead(A1);
  val[2] = analogRead(A2);
  val[3] = analogRead(A3);
  val[4] = analogRead(A4);
  val[5] = analogRead(A5);
  val[6] = analogRead(A6);
  val[7] = analogRead(A7);
  val[8] = analogRead(A8);
  val[9] = analogRead(A9);
  val[10] = analogRead(A10);
  val[11] = analogRead(A11);
  val[12] = analogRead(A12);
  val[13] = analogRead(A13);
  val[14] = analogRead(A14);
  val[15] = analogRead(A15);
}
