import time
import os

def salvar_dados_sensor(sensor: str, dado: str, status: str):
    # Obtenção do horário
    timestamp = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())

    # Verifica se o arquivo existe para adicionar cabeçalho se necessário
    arquivo_existe = os.path.exists(f"{sensor}.csv")
    
    with open(f"dados/{sensor}.csv", "a") as arquivo:
        if not arquivo_existe:
            arquivo.write("Data;Valor;Status\n")
        arquivo.write(f"{timestamp};{dado};{status}\n")

def salvamento_dados(sensor: str, dado: str, status: str) -> str:
    #Captura de erros na tentativa de salvar
    try:
        salvar_dados_sensor(sensor, dado, status)
        return "Dados salvos com sucesso"
    except Exception as e:
        return f"Erro ao salvar dados: {e}"
