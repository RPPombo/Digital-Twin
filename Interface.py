import tkinter as tk
import pandas as pd
import os

def criar_janela_principal() -> tk.Tk:
    #Criando a janela
    janela = tk.Tk()
    janela.title("Digital Twin-Janela Principal")
    centralizar_janela(janela, 1200, 800)

    #Divindo a janela em frames
    frame_esquerda = tk.Frame(janela, bg="lightgreen", width=500, height=800)
    frame_esquerda.grid(column=0 ,row= 0 ,sticky= "nsew")

    frame_direita = tk.Frame(janela, bg="lightblue", width=700, height=800)
    frame_direita.grid(column=1, row= 0, sticky="nsew")

    janela.grid_columnconfigure(0, weight=1)
    janela.grid_columnconfigure(1, weight=1)
    janela.grid_rowconfigure(0, weight=1)
    
    for arquivo in os.listdir("./dados"):
        nome_sensor = arquivo.split(".")[0]
        tk.Button(frame_esquerda, text= nome_sensor, command= lambda: criar_janela_sensor(janela, nome_sensor)).pack()

    #Retornando a janela
    return janela

def criar_janela_sensor(janela: tk.Tk, sensor: str):
    #Criando a janela
    janela_sensor = tk.Toplevel(janela)
    janela_sensor.title(sensor)
    centralizar_janela(janela_sensor, 600, 400)

    #Atribuindo uma scrollbar
    canvas = tk.Canvas(janela_sensor)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(janela_sensor, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas.configure(yscrollcommand=scrollbar.set)

    frame_scroll = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame_scroll, anchor="nw")

    def ajustar_scroll(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    frame_scroll.bind("<Configure>", ajustar_scroll)

    #Dividindo a janela em frames
    frame_esquerda = tk.Frame(frame_scroll, bg="blue", width=200)
    frame_esquerda.grid(row=0, column=0, sticky="n")

    frame_meio = tk.Frame(frame_scroll, bg="red", width=200)
    frame_meio.grid(row=0, column=1, sticky="n")

    frame_direita = tk.Frame(frame_scroll, bg="yellow", width=200)
    frame_direita.grid(row=0, column=2, sticky="n")

    frame_scroll.grid_columnconfigure(0, minsize=200)
    frame_scroll.grid_columnconfigure(1, minsize=200)
    frame_scroll.grid_columnconfigure(2, minsize=200)

    #Escrevendo os dados do arquivo
    try:
        df = pd.read_csv(f"dados/{sensor}.csv")
        tk.Label(frame_esquerda, text= "Data").pack()
        tk.Label(frame_meio, text= f"Valor (Média{df['Valor'].mean()})").pack()
        tk.Label(frame_direita, text= "Status").pack
        
        for index, row in df.iterrows():
            tk.Label(frame_esquerda, text=row['Data']).pack()
            tk.Label(frame_meio, text=row['Valor']).pack()
            tk.Label(frame_direita, text=row['Status']).pack()

    except FileNotFoundError:
        tk.Label(frame_meio, text=f"Arquivo {sensor}.csv não encontrado").pack()
        

def centralizar_janela(janela: tk.Tk, largura: int, altura: int):
    #Conseguindo o tamanho da tela
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()

    #Calculando as coordenadas
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)

    #Aplicando as coordenadas
    janela.geometry(f"{largura}x{altura}+{x}+{y}")

janela = criar_janela_principal()
janela.mainloop()