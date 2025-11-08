# 🚀 Projeto Digital Twin
## 🎯 Introdução  
Este projeto foi desenvolvido como parte de um desafio conjunto entre a empresa FESTO e a FIAP.  
O objetivo é criar um gêmeo digital (Digital Twin) capaz de monitorar em tempo real o funcionamento de uma prensa pneumática aquecida, otimizando o desempenho, aumentando a segurança do operador e permitindo manutenção preditiva.  

## 👥 Equipe
- [@RPPombo](https://github.com/RPPombo) - Desenvolvimento do sistema embarcado (sensores) e montagem da máquina física.
- [@JoaoGabrielVianna](https://github.com/JoaoGabrielVianna) - Criação da interface 3D interativa e modelagem do Digital Twin.
- [@bem-casado](https://github.com/bem-casado) - Implementação da comunicação entre o sistema embarcado e o painel digital.

## 🏭 Máquina Industrial
A máquina simulada é uma prensa industrial responsável por imprimir logotipos em pães de hambúrguer, integrando sistemas pneumáticos e térmicos.

Componentes principais:
| Tipo                 | Modelo         | Função                                   |
| -------------------- | -------------- | ---------------------------------------- |
| Pistão pneumático    | SDA20X50SM     | Movimento vertical da prensa             |
| Válvula solenoide    | 4V21008        | Controle do ar comprimido                |
| Aquecedor            | Hotend 3D 40W  | Aquecimento da superfície de gravação    |
| Sensor ultrassônico  | HC-SR04        | Medição de distância (posição da prensa) |
| Sensor infravermelho | TCRT-5000 (x2) | Detecção de pão e segurança (mão)        |
| Termopar             | Tipo K         | Leitura da temperatura do carimbo        |
| Sensor de pressão    | XGZP701DBR1R   | Monitoramento da pressão pneumática      |



Esses sensores permitem coletar informações sobre temperatura, posição, pressão e segurança do operador em tempo real.

## 🛠️ Tecnologias Utilizadas
| Camada            | Tecnologia                       | Função                                        |
| ----------------- | -------------------------------- | --------------------------------------------- |
| 🧠 Embarcado      | **C++ / PlatformIO (Arduino)**     | Controle da prensa e leitura dos sensores     |
| 🐍 Backend        | **Python (Clean Architecture)**  | Processamento, calibração e API REST          |
| 🕹️ Frontend      | **Vite + TypeScript + Three.js** | Painel 3D interativo e visualização dos dados |
| 🐳 Infraestrutura | **Docker + Docker Compose**      | Ambiente padronizado e orquestração           |
| 🔌 Comunicação    | **Serial / HTTP / WebSocket**    | Comunicação entre firmware, backend e UI      |


## 🏗️ Arquitetura do Projeto

```bash
Digital-Twin/
├─ 📁 cmd/                         # Ponto de entrada do backend (main.py)
│   └─ main.py
│
├─ 📁 data/                        # Armazenamento local e dados processados
│
├─ 📁 internal/
│   └─ 📁 sensor/
│       ├─ 📁 delivery/            # Interface HTTP (API REST)
│       │   └─ http_handler.py
│       ├─ 📁 domain/              # Modelos e entidades do domínio
│       │   └─ sensor_model.py
│       ├─ 📁 repository/          # Comunicação com sensores e banco
│       │   └─ sensor_repository.py
│       └─ 📁 usecase/             # Lógica de negócio e orquestração
│           └─ sensor_usecase.py
│
├─ 📁 shared/
│   ├─ calib.py                    # Calibração de sensores
│   ├─ filter.py                   # Filtros de leitura
│   └─ serial_reader.py            # Comunicação serial com o ESP32
│
├─ 📁 scripts/
│   └─ send_fake.py                # Simulador de dados de sensores
│
├─ 📁 monitor-panel/               # Painel de monitoramento (versão 1)
│   ├─ public/
│   │   ├─ models/
│   │   │   └─ prensa_completa.glb
│   │   └─ vite.svg
│   ├─ src/                        # Código-fonte do painel
│   ├─ index.html
│   ├─ package.json
│   └─ vite.config.ts
│
├─ 📁 monitor-panel-v2/            # Painel atualizado (Vite + Three.js)
│   ├─ public/
│   │   ├─ hdr/
│   │   │   └─ potsdamer_platz_4k.exr
│   │   ├─ models/
│   │   │   ├─ prensa_completa.glb
│   │   │   ├─ prensa_completa-2.glb
│   │   │   └─ prensa_completa-old.glb
│   │   └─ vite.svg
│   ├─ src/
│   ├─ index.html
│   ├─ package.json
│   └─ vite.config.ts
│
├─ 📁 src/ (C++)                   # Firmware embarcado (PlatformIO)
│   └─ main.cpp
│
├─ Dockerfile                      # Build do backend
├─ docker-compose.yml              # Orquestração dos serviços
├─ requirements.txt                # Dependências Python
├─ .env                            # Configurações de ambiente
└─ README.md

```
## 🧩 Arquitetura de Comunicação
```mathematica
┌────────────────────────┐
│   Firmware (Arduino)    │
│  • C++ / PlatformIO     │
│  • Leitura dos sensores │
│  • Envio via Serial     │
└──────────┬──────────────┘
           │
           ▼
┌────────────────────────┐
│   Backend (Python)     │
│  • Clean Architecture  │
│  • Filtros e calibração│
│  • API REST / WebSocket│
└──────────┬──────────────┘
           │
           ▼
┌────────────────────────┐
│   Frontend (Vite + TS) │
│  • Render 3D (Three.js)│
│  • Visualização RT     │
└────────────────────────┘
```

## 🔄 Fluxo de Funcionamento
1. Leitura de Sensores – O firmware coleta temperatura, posição e pressão em tempo real.
2. Transmissão Serial – Os dados são enviados ao backend via porta serial.
3. Processamento Backend – O backend aplica calibrações, filtros e validações.
4. Exposição via API – Os dados processados são expostos via REST e WebSocket.
5. Visualização 3D – O painel digital atualiza o modelo da prensa em tempo real, refletindo as condições reais da máquina.

## 🧪 Testes e Simulações
O script send_fake.py permite testar a API sem conectar o hardware real.  
Os dados simulados seguem o mesmo formato da leitura real dos sensores.  

## 🚢 Execução via Docker
```bash
# Build dos containers
docker-compose build

# Inicialização dos serviços
docker-compose up
```  

O container Python executará o backend e disponibilizará a API localmente para o painel monitorar os dados.

## 🌐 Painel 3D Interativo

A interface visual permite:
* Visualizar o estado da prensa em tempo real
* Acompanhar sensores de temperatura, pressão e posição
* Simular eventos e testar a resposta do sistema
