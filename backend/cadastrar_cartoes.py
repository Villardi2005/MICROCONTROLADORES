
from werkzeug.security import generate_password_hash
from banco import conectar, criar_tabelas

criar_tabelas()

conexao = conectar()
cursor = conexao.cursor()

cartoes = [
    ("123456", 10000, 1, "1234"),
    ("654321", 20000, 1, "4321")
]

for id_cartao, saldo, ativo, pin in cartoes:
    cursor.execute("""
        INSERT OR IGNORE INTO cartoes
        (id_cartao, saldo, ativo, pin_hash)
        VALUES (?, ?, ?, ?)
    """, (
        id_cartao,
        saldo,
        ativo,
        generate_password_hash(pin)
    ))

    if cursor.rowcount == 1:
        print(f"Cartão {id_cartao} cadastrado com sucesso!")
    else:
        print(f"Cartão {id_cartao} já existe. Mantido sem alterações.")

conexao.commit()
conexao.close()

print("Cadastro de cartões finalizado!")
