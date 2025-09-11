# 🚀 Projeto Digital Twin
## 🎯 Introdução  
Este projeto foi desenvolvido como um desafio conjunto da empresa FESTO e da faculdade FIAP.
O objetivo principal é criar um gêmeo digital para monitorar em tempo real o funcionamento de uma máquina industrial pneumática.

## 🏭 Máquina Industrial
A máquina escolhida para o Digital Twin é uma prensa que imprime a logo de empresas em pães de hambúrguer.

Componentes principais:
- Pistão pneumático (SDA20X50SM)
- Válvula solenoide pneumática (4V21008)
- Aquecedor (Hotend Impressora 3D 40W)
- Sensores:
    - HC-SR04
    - TCRT-5000
    - Termopar tipo K
    - XGZP701DBR1R

## 🛠️ Tecnologias Utilizadas
- 🐍 Python: backend do Digital Twin e API REST
- 💻 C++: sistema embarcado para controle da máquina e obtenção de dados
- 🕹️ Unity: interface gráfica 3D para o Digital Twin, visualização e interação

## 🏗️ Arquitetura do Projeto

```bash
Digital-Twin/
├─ cmd/
│  └─ main.py
├─ internal/
│  ├─ sensor/
│  │  ├─ delivery/
│  │  │  └─ http_handler.py
│  │  ├─ domain/
│  │  │  └─ sensor_model.py
│  │  ├─ repository/
│  │  │  └─ sensor_repository.py
│  │  └─ usecase/
│  │     └─ sensor_usecase.py
│  └─ shared/
│     └─ serial_reader.py
├─ .gitignore
└─ README.md
```

## ⚙️ Fluxo de funcionamento
- 🔍 Detecta automaticamente o sensor (Arduino) conectado via porta serial.
- 📡 Lê dados em tempo real da máquina (ex: pressão, posição).
- 💾 Salva esses dados localmente em arquivos CSV.
- 🌐 Expõe uma API REST para consulta dos dados de forma organizada.