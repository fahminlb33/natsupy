#include <DHT.h>

DHT dht(D3, DHT22);

void setup() {
  Serial.begin(9600);
  Serial.println(F("NatsuPy DHT22 Demo!"));

  dht.begin();
}

void loop() {
  float t = dht.readTemperature();

  if (isnan(t)) {
    return;
  }

  Serial.println(t);
  delay(500);
}
