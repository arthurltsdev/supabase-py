import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# ─── Caminho do CSV unificado ─────────────────────────────
csv_path = "extratos_pix/recebimentos_unificados.csv"

# ─── Função para converter data do XLS/XLXS ──────────────
def converter_data(data_str):
    try:
        dia = int(data_str[:2])
        mes_txt = data_str[3:6]
        mapa_meses = {
            "Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4,
            "Mai": 5, "Jun": 6, "Jul": 7, "Ago": 8,
            "Set": 9, "Out": 10, "Dez": 12
        }
        mes = mapa_meses.get(mes_txt, None)
        if mes is None:
            return None
        ano = 2024 if mes_txt == "Dez" else 2025
        return f"{dia:02d}/{mes:02d}/{ano}"
    except:
        return None

# ─── Função para detectar separador em CSV ──────────────
def detectar_separador(caminho):
    with open(caminho, 'r', encoding="utf-8") as f:
        primeira_linha = f.readline()
        if primeira_linha.count(";") > primeira_linha.count(","):
            return ";"
        else:
            return ","

# ─── Função para processar arquivos selecionados ──────────
def processar_arquivos():
    arquivos = filedialog.askopenfilenames(
        title="Selecione arquivos (.xls, .xlsx ou .csv)",
        filetypes=[("Arquivos Excel ou CSV", "*.xls *.xlsx *.csv")]
    )
    
    if not arquivos:
        return

    if os.path.exists(csv_path):
        df_existente = pd.read_csv(csv_path, sep=";")
        ids_existentes = set(df_existente["idOperacao"].astype(str))
    else:
        df_existente = pd.DataFrame(columns=["dataEHora", "chavesPix", "idOperacao", "origemDestinatario", "valor"])
        ids_existentes = set()

    novos_registros = 0

    for arq in arquivos:
        try:
            if arq.endswith(".xls"):
                df = pd.read_excel(arq, engine="xlrd")
                df["dataEHora"] = df["dataEHora"].apply(converter_data)

            elif arq.endswith(".xlsx"):
                df = pd.read_excel(arq, engine="openpyxl")
                df["dataEHora"] = df["dataEHora"].apply(converter_data)

            elif arq.endswith(".csv"):
                sep = detectar_separador(arq)
                df = pd.read_csv(arq, sep=sep)
                if not all(df["dataEHora"].astype(str).str.match(r"\\d{2}/\\d{2}/\\d{4}")):
                    messagebox.showerror("Erro", f"Formato de data inválido em {arq}. Deve ser DD/MM/YYYY.")
                    continue
            else:
                continue

            cols = ["dataEHora", "chavesPix", "idOperacao", "origemDestinatario", "valor"]
            df = df[cols]
            df = df[df["dataEHora"].notna()]
            df = df[~df["idOperacao"].astype(str).isin(ids_existentes)]
            
            novos_registros += len(df)
            df_existente = pd.concat([df_existente, df], ignore_index=True)
            ids_existentes.update(df["idOperacao"].astype(str))

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar {arq}: {e}")
            continue

    # Ordenar por dataEHora
    df_existente["dataEHora_dt"] = pd.to_datetime(df_existente["dataEHora"], format="%d/%m/%Y", errors="coerce")
    df_existente = df_existente.sort_values("dataEHora_dt").drop(columns=["dataEHora_dt"])

    # Salvar CSV final
    df_existente.to_csv(csv_path, sep=";", index=False, encoding="utf-8")

    messagebox.showinfo("Finalizado", f"✅ Processamento concluído!\\n➕ Novos registros adicionados: {novos_registros}\\n📄 Total atual no CSV: {len(df_existente)}")

# ─── Interface gráfica ────────────────────────────────────
janela = tk.Tk()
janela.title("Unificador de Extratos PIX")

botao = tk.Button(
    janela,
    text="Adicionar Extrato(s)",
    command=processar_arquivos,
    width=30,
    height=2,
    bg="green",
    fg="white",
    font=("Arial", 12, "bold")
)
botao.pack(pady=20)

janela.mainloop()
