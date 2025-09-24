#include <Arduino.h>
#include <max6675.h>

// --- Sensores Infravermelho ---
#define IR_MAO A0
#define IR_PAO 8

// --- Sensor de Pressão ---
#define PRESSAO A4

// --- Sensor de Distância ---
#define ECHO 10
#define TRIG 9

// --- Sensor de Temperatura (MAX6675) ---
const int thermoDO  = 12; // SO
const int thermoCS  = 11; // CS
const int thermoCLK = 13; // SCK
MAX6675 termopar(thermoCLK, thermoCS, thermoDO);

// --- RELÉS (ativo em LOW) ---
#define RELE_VALVULA   6
#define RELE_AQUECEDOR 7

// --- Estado ---
float distancia_inicial = 0.0;
bool  retraido           = true;
bool  aquecedorLigado    = false;
bool  valvulaAberta      = false;
unsigned long tempo_salvo = 0;
unsigned long cooldown    = 0;

const float SOM_MM_POR_US     = 0.343;   // 343 m/s = 0.343 mm/us
const unsigned long ECHO_TOUS = 30000UL; // timeout do pulseIn (~5 m)

// Função para medir distância (mm); retorna <0 se timeout
float medirDistanciaMM() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  unsigned long duracao = pulseIn(ECHO, HIGH, ECHO_TOUS);
  if (duracao == 0) return -1.0; // sem eco
  return (duracao * SOM_MM_POR_US) / 2.0;
}

void setup() {
  Serial.begin(9600);

  pinMode(IR_PAO, INPUT);
  pinMode(IR_MAO, INPUT);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(RELE_AQUECEDOR, OUTPUT);
  digitalWrite(RELE_AQUECEDOR, HIGH); // desligado

  pinMode(RELE_VALVULA, OUTPUT);
  digitalWrite(RELE_VALVULA, HIGH); // desligado

  // Mede distância inicial (faz média de 5 leituras)
  float soma = 0;
  const int N = 5;
  for (int i = 0; i < N; i++) {
    float d = medirDistanciaMM();
    if (d >= 0) soma += d;
    delay(50);
  }
  distancia_inicial = soma / N;

  delay(500);
}

void loop() {
  // --- Termopar ---
  float temperatura = termopar.readCelsius();

  // --- Pressão ---
  int leituraPressao = analogRead(PRESSAO);
  float pressao = leituraPressao * 0.08; 

  // --- Sensores IR ---
  bool pao = (digitalRead(IR_PAO) == HIGH);  // se seu IR for ativo em LOW, inverta
  int  leituramao = analogRead(IR_MAO);
  bool mao = (leituramao <= 900);            // ajustar threshold no hardware

  // --- HC-SR04 ---
  float distancia_mm = medirDistanciaMM();

  // --- Timestamp ---
  unsigned long agora = millis();

  // --- Atualiza retração ---
  if (distancia_mm >= 0) {
    float diff = distancia_mm - distancia_inicial;
    if (diff < 0) diff = -diff;
    retraido = (diff <= 10.0); // tolerância de 10 mm
  }

  // --- Controle de temperatura com histerese ---
  if (temperatura < 180.0) {
    aquecedorLigado = true;
  } else if (temperatura >= 185.0) {
    aquecedorLigado = false;
  }
  digitalWrite(RELE_AQUECEDOR, aquecedorLigado ? LOW : HIGH);
  bool temperatura_ideal = !aquecedorLigado;

  // --- Ação da válvula: 2s aberta + 10s cooldown ---
  if (!valvulaAberta && (agora - cooldown > 10000)) {
    if (pao && !mao && temperatura_ideal && retraido) {
      digitalWrite(RELE_VALVULA, LOW); // abre (ativo em LOW)
      tempo_salvo = agora;
      valvulaAberta = true;
    }
  }
  if (valvulaAberta && (agora - tempo_salvo > 2000)) {
    digitalWrite(RELE_VALVULA, HIGH); // fecha
    valvulaAberta = false;
    cooldown = agora; // inicia cooldown só após ter aberto
  }

  // --- Envio em JSON ---
  Serial.print("{");
  Serial.print("\"timestamp_ms\":"); Serial.print(agora); Serial.print(",");
  Serial.print("\"temperatura_C\":"); Serial.print(temperatura, 2); Serial.print(",");
  Serial.print("\"pressao_un\":"); Serial.print(pressao, 2); Serial.print(",");
  Serial.print("\"IR_pao\":"); Serial.print(pao ? "true" : "false"); Serial.print(",");
  Serial.print("\"IR_mao\":"); Serial.print(mao ? "true" : "false"); Serial.print(",");
  Serial.print("\"distancia_mm\":");
  if (distancia_mm < 0) Serial.print("null"); else Serial.print(distancia_mm, 1);
  Serial.println("}");
  delay(500);
}
