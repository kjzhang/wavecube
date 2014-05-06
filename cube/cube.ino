#include <SoftwareSerial.h>
#include <Tlc5940.h>
#include <tlc_config.h>

const int NUM_LAYERS = 4;
const int NUM_COLUMNS = 16;
const int NUM_COLORS = 3;
const int NUM_CHANNELS = NUM_COLUMNS * NUM_COLORS;

const int LAYER_0 = A0;
const int LAYER_1 = A1;
const int LAYER_2 = A2;
const int LAYER_3 = A3;

const int COLOR_R = 0;
const int COLOR_G = 1;
const int COLOR_B = 2;

const int MAX_POWER = 2048;

char cubeBuffer[NUM_LAYERS][NUM_CHANNELS];

const uint8_t COLOR_MAP[] = {
  // R_MAP
  0,  2, 44, 47,
  7,  6, 41, 40,
  14, 12, 35, 33,
  17, 19, 27, 31,
  // G_MAP
  3,  5, 43, 46,
  11,  8, 37, 39,
  21, 23, 28, 34,
  20, 22, 29, 32,
  // B_MAP
  1,  4, 42, 45,
  10,  9, 38, 36,
  15, 13, 25, 24,
  16, 18, 26, 30
};

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(60000);
  Serial.println("SWAGASAURUS");

  Tlc.init(0);
  Tlc.update();

  pinMode(LAYER_0, OUTPUT);
  pinMode(LAYER_1, OUTPUT);
  pinMode(LAYER_2, OUTPUT);
  pinMode(LAYER_3, OUTPUT);

  digitalWrite(LAYER_0, LOW);
  digitalWrite(LAYER_1, LOW);
  digitalWrite(LAYER_2, LOW);
  digitalWrite(LAYER_3, LOW);

  powerLayer(0);
}

void loop() {
  // sampleRGB();
  // sampleMultiplex();

  if (Serial.available()) {
    for (int layer = 0; layer < NUM_LAYERS; layer++) {
      Serial.readBytes(cubeBuffer[layer], NUM_CHANNELS);
    }
  }
  renderCube(5);
}

void renderCube(int interval) {
  unsigned char **cube = (unsigned char **) cubeBuffer;
  for (int layer = 0; layer < NUM_LAYERS; layer++) {
    renderLayer(layer, cube[layer]);
    delay(interval);
  }
}

void renderLayer(int layer, unsigned char cubeLayer[]) {
  for (int c = 0; c < NUM_CHANNELS; c++) {
    int power = MAX_POWER * ((int) cubeLayer[c]) / 256;
    if (power > MAX_POWER) {
      power = MAX_POWER;
    } 
    
    Tlc.set(getOutput(c), power); 
  }

  powerLayer(-1);
  Tlc.update();
  powerLayer(layer);
}

void powerColor(int color, int power) {
  int offset = NUM_COLUMNS * color;
  for (int i = offset; i < offset + NUM_COLUMNS; i++) {
    Tlc.set(COLOR_MAP[i], power);
  }
  Tlc.update();
}

void powerLayer(int layer) {
  switch (layer) {
  case 0:
    digitalWrite(LAYER_1, LOW);
    digitalWrite(LAYER_2, LOW);
    digitalWrite(LAYER_3, LOW);
    digitalWrite(LAYER_0, HIGH);
    break;
  case 1:
    digitalWrite(LAYER_0, LOW);
    digitalWrite(LAYER_2, LOW);
    digitalWrite(LAYER_3, LOW);
    digitalWrite(LAYER_1, HIGH);
    break;
  case 2:
    digitalWrite(LAYER_0, LOW);
    digitalWrite(LAYER_1, LOW);
    digitalWrite(LAYER_3, LOW);
    digitalWrite(LAYER_2, HIGH);
    break;
  case 3:
    digitalWrite(LAYER_0, LOW);
    digitalWrite(LAYER_1, LOW);
    digitalWrite(LAYER_2, LOW);
    digitalWrite(LAYER_3, HIGH);
    break;
  default:
    digitalWrite(LAYER_0, LOW);
    digitalWrite(LAYER_1, LOW);
    digitalWrite(LAYER_2, LOW);
    digitalWrite(LAYER_3, LOW);
    break;
  }
}

int getOutput(int channel) {
  return COLOR_MAP[channel];
}

void sampleRGB() {
  for (int channel = 0; channel < 16 * NUM_TLCS; channel++) {
    Tlc.clear();
    Tlc.set(getOutput(channel), 2048);
    Tlc.update();
    delay(50);
  }
}

void sampleMultiplex() {
  powerColor(COLOR_B, 1024);
  for (int layer = 0; layer < NUM_LAYERS; layer++) {
    powerLayer(layer);
    delay(5);
  }
}




