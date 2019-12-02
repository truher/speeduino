/* Types for testing */

bool v1;
boolean v2;
byte v3;
char v4;
double v5;
float v6;
int v7;
long v8;
short v9;
size_t v10;
unsigned char v11;
unsigned int v12;
unsigned long v13;
word v14;

bool av1[2] = {false, true};
boolean av2[2] = {true, false};
byte av3[2] = {'\x01','\x02'};
char av4[2] = {'\x09','\x08'};
double av5[2] = {1.4, 1.5};
float av6[2] = {1.2, 1.3};
int av7[2] = {9, 8};
// gcc seems not to be allocating enough space for this
long av8[2] = {100000,100000};
short av9[2] = {2, 4};
size_t av10[2] = {3, 2};
unsigned char av11[2] = {'\x04','\x08'};
unsigned int av12[2] = {4,1};
unsigned long av13[2] = {9,8};
word av14[2] = {9, 7};

struct s1 {
  bool  s1v1;
  boolean  s1v2;
  byte  s1v3;
  char  s1v4;
  double  s1v5;
  float  s1v6;
  int  s1v7;
  long  s1v8;
  short  s1v9;
  size_t  s1v10;
  unsigned char s1v11;
  unsigned int  s1v12;
  unsigned long  s1v13;
  word s1v14;

  // the general case is pretty confusing.  also i think the DWARF output is wrong
  // see http://dwarfstd.org/ShowIssue.php?issue=081130.1
  // the only thing we actually do is "byte", with no padding, and without byte straddling.
  // so just do that.
  // TODO: handle padding, byte straddling, wider types, etc.
  byte s1v15 : 4; // 31
  byte s1v16 : 4; // 31
  byte s1v17 : 4; // 32
  byte s1v18 : 1; // 32
  byte s1v19 : 3; // 32
  byte s1v20 : 2; // 33
  byte s1v21 : 2; // 33
  byte s1v22 : 2; // 33
};
struct s1 sv1;

int *vv0;
char *vv1;

void setup() {
  // everything needs to be referenced or it won't have alloc
  v1 = true;
  v2 = true;
  v3 = '\x10';
  v4 = '\x11';
  v5 = 4.14;
  v6 = 5.15;
  v7 = 15;
  v8 = 16;
  v9 = 17;
  v10 = 18;
  v11 = '\x12';
  v12 = 19;
  v13 = 20;
  v14 = 21;

  av1[0] = false;
  av2[0] = true;
  av3[0] = '\x01';
  av4[0] = '\x09';
  av5[0] = 1.4;
  av6[0] = 1.2;
  av7[0] = 9;
  av8[0] = 1;
  av9[0] = 2;
  av10[0] = 3;
  av11[0] = '\x04';
  av12[0] = 4;
  av13[0] = 9;
  av14[0] = 9;

  av1[1] = true;
  av2[1] = false;
  av3[1] = '\x02';
  av4[1] = '\x08';
  av5[1] = 1.5;
  av6[1] = 1.3;
  av7[1] = 8;
  av8[1] = 2;
  av9[1] = 4;
  av10[1] = 2;
  av11[1] = '\x08';
  av12[1] = 1;
  av13[1] = 8;
  av14[1] = 7;
  
  sv1.s1v1 = true;
  sv1.s1v2 = true;
  sv1.s1v3 = '\x01';
  sv1.s1v4 = '\x02';
  sv1.s1v5 = 3.14159;
  sv1.s1v6 = 3.14159;
  sv1.s1v7 = 3;
  sv1.s1v8 = 4;
  sv1.s1v9 = 5;
  sv1.s1v10 = 1;  // ??
  sv1.s1v11 = '\x03';
  sv1.s1v12 = 6;
  sv1.s1v13 = 7;
  sv1.s1v14 = 8;

  sv1.s1v15 = 15;
  sv1.s1v16 = 4;
  sv1.s1v17 = 3;
  sv1.s1v18 = 1;
  sv1.s1v19 = 3;
  sv1.s1v20 = 3;
  sv1.s1v21 = 2;
  sv1.s1v22 = 2;

  vv0 = (int *)malloc(2 * sizeof(int));
  *vv0 = 34;
  *(vv0+1) = 56;
  vv1 = (char *)malloc(2 * sizeof(int));
  *vv1 = '\x10';
  *(vv1+1) = '\x11';

}

void loop() {
  //exit(0);
}
