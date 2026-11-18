import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).parent / "maquininha.db"


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cartoes (
            id_cartao TEXT PRIMARY KEY,
            saldo INTEGER NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            pin_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cartao TEXT NOT NULL,
            valor INTEGER NOT NULL,
            status TEXT NOT NULL,
            motivo TEXT,
            data_hora TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS terminais (
        id_terminal TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        ativo INTEGER NOT NULL DEFAULT 1
    )
    """)

    conexao.commit()
    conexao.close()


if __name__ == "__main__":
    criar_tabelas()
    print("Banco de dados criado com sucesso!")
