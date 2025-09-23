#include <Arduino.h>
#include <max6675.h>

// --- Termopar MAX6675 ---
int thermoDO = 12;
int thermoCS = 10;
int thermoCLK = 13;
MAX6675 termopar(thermoCLK, thermoCS, thermoDO);

// --- Pressão (AD620 + XGZP701DB1R) ---
#define PINO_PRESSAO A0

// --- Sensores infravermelho (TCRT5000) ---
#define IR_PAO A2
#define IR_MAO A1

// --- HC-SR04 ---
#define TRIG 4
#define ECHO 5

// --- RELÉS ---
#define RELE_VALVULA 6
#define RELE_AQUECEDOR 7

// --- Variáveis de estado ---
float distancia_inicial = 0;
bool retraido = true;
bool aquecedorLigado = false;
unsigned long tempo_salvo = 0;
unsigned long cooldown = 0;

void setup() {
  Serial.begin(9600);

  pinMode(IR_PAO, INPUT);
  pinMode(IR_MAO, INPUT);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(RELE_AQUECEDOR, OUTPUT);
  digitalWrite(RELE_AQUECEDOR, HIGH); // desligado inicialmente

  pinMode(RELE_VALVULA, OUTPUT);
  digitalWrite(RELE_VALVULA, HIGH); // desligado inicialmente

  // Mede distância inicial (braço retraído)
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duracao = pulseIn(ECHO, HIGH);
  distancia_inicial = (duracao * 0.343) / 2; // mm

  delay(500);
}

void loop() {
  // --- Termopar ---
  float temperatura = termopar.readCelsius();

  // --- Pressão ---
  int leituraPressao = analogRead(PINO_PRESSAO);
  float tensao = (leituraPressao / 1023.0) * 5.0;
  float pressao_kPa = tensao * 100.0; // ajustar via calibração

  // --- Sensores IR ---
  bool leiturapao = analogRead(IR_PAO); // detecta pão
  bool pao;
  if (leiturapao >= 500) {
    pao = true;
  } else {
    pao = false;
  }
  float leituramao = analogRead(IR_MAO); // detecta mão
  bool mao;
  if (leituramao >= 500) {
    mao = true;
  } else {
    mao = false;
  }


  // --- HC-SR04 ---
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duracao = pulseIn(ECHO, HIGH);
  float distancia_mm = (duracao * 0.343) / 2; // mm

    // --- Timestamp ---
  unsigned long timestamp = millis();

  // --- Atualiza retração ---
  retraido = (distancia_mm >= distancia_inicial - 2 && distancia_mm <= distancia_inicial + 2);

  // --- Controle de temperatura com histerese ---
  if (temperatura < 180) {
    aquecedorLigado = true;
  } else if (temperatura >= 185) {
    aquecedorLigado = false;
  }
  digitalWrite(RELE_AQUECEDOR, aquecedorLigado ? LOW : HIGH);
  bool temperatura_ideal = !aquecedorLigado;

  // --- Ação da válvula ---
  if (millis() - cooldown > 10000){
    if (pao && !mao && temperatura_ideal && retraido) {
      digitalWrite(RELE_VALVULA, LOW);
      tempo_salvo = millis();
    }
  }
  if (millis() - tempo_salvo > 2000) {
    digitalWrite(RELE_VALVULA, HIGH);
    cooldown = millis();
  }

  // --- Envio em JSON ---
  Serial.print("{");
  Serial.print("\"timestamp_ms\":"); Serial.print(timestamp); Serial.print(",");
  Serial.print("\"temperatura_C\":"); Serial.print(temperatura, 2); Serial.print(",");
  Serial.print("\"pressao_kPa\":"); Serial.print(pressao_kPa, 2); Serial.print(",");
  Serial.print("\"IR_pao\":"); Serial.print(pao); Serial.print(",");
  Serial.print("\"IR_mao\":"); Serial.print(mao); Serial.print(",");
  Serial.print("\"distancia_mm\":"); Serial.print(distancia_mm, 1);
  Serial.println("}");
  delay(500);
}
