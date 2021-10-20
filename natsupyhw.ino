#include "DHT.h"

DHT dht(D3, DHT22);

void setup() {
  Serial.begin(9600);
  Serial.println(F("NatsuPy Demo!"));

  dht.begin();
}

void loop() {
  delay(1000);
  float t = dht.readTemperature();

  if (isnan(t)) {
    return;
  }

  Serial.println(t);
}
