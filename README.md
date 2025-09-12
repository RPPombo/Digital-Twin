# 🚀 Projeto Digital Twin
## 🎯 Introdução  
Este projeto foi desenvolvido como parte de um desafio conjunto entre a empresa FESTO e a faculdade FIAP. O objetivo principal é criar um gêmeo digital para monitorar em tempo real o funcionamento de uma máquina industrial pneumática, com foco na otimização do desempenho e manutenção preditiva.

## Equipe
- [@RPPombo](https://github.com/RPPombo) - Responsável pela criação do sistema embarcado de sensores e da criação do sistema físico
- [@JoaoGabrielVianna](https://github.com/JoaoGabrielVianna) - Responsável pela interface visual e modelagem do Digital Twin
- [@bem-casado](https://github.com/bem-casado) - Responsável pela comunicação entre sistema embarcado e a interface

## 🏭 Máquina Industrial
A máquina escolhida para o Digital Twin é uma prensa que imprime a logo de empresas em pães de hambúrguer.

Componentes principais:
- Pistão pneumático (SDA20X50SM)
- Válvula solenoide pneumática (4V21008)
- Aquecedor (Hotend Impressora 3D 40W)
- Sensores:
    | **Tipo de Sensor**               | **Modelo**   | **Quantidade** |
    | -------------------------------- | ------------ | -------------- |
    | Sensor Ultrassônico              | HC-SR04      | 1              |
    | Sensor de Reflexão Infravermelho | TCRT-5000    | 2              |
    | Termopar                         | Tipo K       | 1              |
    | Sensor de Distância              | XGZP701DBR1R | 1              |


Os sensores recebem informções sobre a temperatura do "carimbo", a posição da prensa, pressão do sistema, verificação de pão abaixo da prensa e verificação de mão para segurança do utilizador.

## 🛠️ Tecnologias Utilizadas
- 🐍 Python: Backend do Digital Twin e API REST, utilizado para processamento de dados e comunicação com o sistema embarcado.
- 💻 C++: Sistema embarcado responsável pelo controle da máquina e leitura dos dados dos sensores.
- 🕹️ Unity: Ferramenta de modelagem 3D utilizada para criar a interface gráfica interativa do gêmeo digital.

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
1. **Detecção automática**: O sistema detecta automaticamente o sensor conectado via porta serial (Arduino).
2. **Leitura dos dados**: Os dados da máquina (como pressão, posição, etc.) são lidos em tempo real.
3. **Armazenamento**: As informações são salvas localmente em arquivos CSV para análise posterior.
4. **Exposição da API**: A API REST é disponibilizada para permitir consultas e visualizações dos dados de forma organizada e acessível.
