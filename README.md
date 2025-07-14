# 🚀 Projeto Digital Twin
## 🎯 Introdução  
Este projeto foi desenvolvido como um desafio conjunto da empresa FESTO e da faculdade FIAP.
O objetivo principal é criar um gêmeo digital para monitorar em tempo real o funcionamento de uma máquina industrial pneumática.

## 🏭 Máquina Industrial

A máquina escolhida para o Digital Twin é uma prensa que imprime a logo de empresas em pães de hambúrguer.

Componentes principais:
- ...

## 🛠️ Tecnologias Utilizadas
- 🐍 Python: backend do Digital Twin e API REST
- 💻 C++: sistema embarcado para controle da máquina
- 🕹️ Unity: interface gráfica 3D para o Digital Twin, visualização e interação

## 🏗️ Arquitetura do Projeto

```bash
Digital-Twin/
├─ cmd/
│  ├─ __pycache__/
│  │  └─ main.cpython-313.pyc
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
│     ├─ assistentes.py
│     ├─ Interface.py
│     └─ Serial.py
├─ .gitignore
└─ README.md
```

## ⚙️ Fluxo de funcionamento

- 🔍 Detecta automaticamente o sensor (Arduino) conectado via porta serial.
- 📡 Lê dados em tempo real da máquina (ex: pressão, posição).
- 💾 Salva esses dados localmente em arquivos CSV.
- 🌐 Expõe uma API REST para consulta dos dados de forma organizada.