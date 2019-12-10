#include "../../../speeduino/src/FastCRC/FastCRC.h"

#include "cobs.h"

FastCRC16 CRC16;

struct Request {
  byte a;
  byte b;
  byte c;
} req;

struct RequestFrame {
  Request r;
  uint16_t crc;
} reqf;

byte sb[64];                // send buffer (cobs encoded)
size_t sbl;                 // send buffer length

struct Response {
  byte x;
  byte y;
} res;

struct ResponseFrame {
  Response r;
  uint16_t crc;
} resf;

byte rb[64];                // receive buffer (cobs encoded)
int rbi = -1;               // receive buffer index
byte drb[64];               // decoded receive buffer
size_t drbl;                // decoded receive buffer length
bool responseValid;         // captures the CRC match result

void processResponseFrame() {
  Serial.println("processResponseFrame");
  //drbl = cobs_decode(rb, rbi, (byte *) & resf);
  drbl = cobs_decode(rb, rbi, drb);
  if (drbl != sizeof(resf)) {
    Serial.println("wrong length");
    Serial.print(" drbl: ");
    Serial.print(drbl);
    Serial.print(" resfy: ");
    Serial.print(sizeof(resf));
    return;
  }
  for (size_t i = 0; i < sizeof(resf); ++i) {
    ((byte *) &resf)[i] = drb[i];
  }
  if (resf.crc == CRC16.xmodem((byte *) &(resf.r), sizeof(resf.r))) {
    responseValid = true;
    //Serial.println("good response packet");
    //Serial.print("length: ");
    //Serial.print(rbi);
    //Serial.println("");
    //Serial.print("payload: ");
    //Serial.write(rb, rbi);
    //Serial.println("");
    //Serial.print("struct: ");
    //Serial.write((byte *)&(resf.r), sizeof(resf.r));
    //Serial.print(" x: ");
    //Serial.print(resf.r.x);
    //Serial.print(" y: ");
    //Serial.print(resf.r.y);
    //Serial.println("");
  } else {
    responseValid = false;
    Serial.print("\nbad response packet\n");
  }
}

void serialEvent3() {
  //Serial.println("serialEvent3");
  while(Serial3.available() > 0) {
    byte b = Serial3.read();
    //Serial.print("serial3 read: ");
    //Serial.println(b);
    if (rbi == -1) {        // waiting for leading \0
      //Serial.println("waiting");
      if (b == 0) {
        Serial.println("found header");
        rbi = 0;  // \0 => ready, otherwise discard
      }
    } else if (b == 0) {
      //Serial.println("complete");
      processResponseFrame();
      rbi = -1;             // could use one \0 both start and end, but nah
    } else if (rbi < 64) {  // got a data byte
      //Serial.println("got data");
      rb[rbi] = b;
      rbi += 1;
    } else {                // overflow, abandon
      //Serial.println("overflow");
      rbi = -1;
    }
  }
}

void setup() {
  Serial.begin(1000000);
  Serial3.begin(1000000);
  //Serial3.setTimeout(100);
}

int loopcounter = 0;
void loop() {
  Serial.print("loop: ");
  Serial.print(loopcounter);
  Serial.println("");
  Serial.print("micros: ");
  Serial.print(micros());
  Serial.println("");
  ++loopcounter;
  //req = {0,2,0};
  //Request req;
  //req.a = 0;
  //req.b = 2;
  //eq.c = 0;
  // not sure this nesting will work
  reqf = {{0,2,0}, CRC16.xmodem((byte *) &(reqf.r), sizeof(reqf.r))};
  sbl = cobs_encode((byte *) &reqf, sizeof(reqf), sb);

  //Serial.println("request");
  //Serial.print("length: ");
  //Serial.print(sizeof(reqf.r));
  //Serial.println("");
  //Serial.print("payload: ");
  //Serial.write((byte *)&(reqf.r), sizeof(reqf.r));
  //Serial.print(" a: ");
  //Serial.print(reqf.r.a);
  //Serial.print(" b: ");
  //Serial.print(reqf.r.b);
  //Serial.print(" c: ");
  //Serial.print(reqf.r.c);
  //Serial.println("");

  Serial3.write(0);
  Serial3.write(sb, sbl);
  Serial3.write(0);

  //delay(300);
}
