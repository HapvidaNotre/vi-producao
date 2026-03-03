import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "vi_producao.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabela de registros de produção
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operador TEXT NOT NULL,
            pedido TEXT NOT NULL,
            etapa TEXT NOT NULL,
            inicio TIMESTAMP NOT NULL,
            fim TIMESTAMP,
            duracao_segundos INTEGER
        )
    """)
    conn.commit()
    conn.close()

def salvar_inicio(operador, pedido, etapa):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO producao (operador, pedido, etapa, inicio) VALUES (?, ?, ?, ?)",
        (operador, pedido, etapa, inicio)
    )
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def finalizar_etapa(registro_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fim = datetime.now()
    fim_str = fim.strftime("%Y-%m-%d %H:%M:%S")
    
    # Buscar o início para calcular a duração
    cursor.execute("SELECT inicio FROM producao WHERE id = ?", (registro_id,))
    row = cursor.fetchone()
    if row:
        inicio = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        duracao = int((fim - inicio).total_seconds())
        cursor.execute(
            "UPDATE producao SET fim = ?, duracao_segundos = ? WHERE id = ?",
            (fim_str, duracao, registro_id)
        )
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM producao WHERE fim IS NOT NULL", conn)
    conn.close()
    return df

if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso.")
