import serial
from serial.tools import list_ports

def ler_dados_serial(porta: str, baudrate: int) -> dict:
    ser = serial.Serial(porta, baudrate, timeout=1)
    dicionario = {}

    while True:
        dado = ser.readline().decode("utf-8").strip()

        if not dado or ":" not in dado:
            continue  # ignora linhas vazias ou malformadas

        chave, valor = dado.split(":", 1)

        if chave.strip() == "Posição":
            dicionario[chave.strip()] = valor.strip()
            
            while True:
                dado = ser.readline().decode("utf-8").strip()

                if not dado or ":" not in dado:
                    continue

                chave, valor = dado.split(":", 1)
                dicionario[chave.strip()] = valor.strip()

                if chave.strip() == "Pressão":
                    break
            break  # sai do loop principal depois de ler até "Pressão"

    ser.close()
    return dicionario

def detectar_arduino() -> str:
    portas = list_ports.comports()
    for porta in portas:
        if "Arduino" in porta.description or "CH340" in porta.description:
            return porta.device
    return "Arduino não encontrado"