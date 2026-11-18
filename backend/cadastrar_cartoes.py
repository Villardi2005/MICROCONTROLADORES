from werkzeug.security import generate_password_hash
from banco import conectar, criar_tabelas

criar_tabelas()

conexao = conectar()
cursor = conexao.cursor()

cursor.execute("""
    INSERT OR REPLACE INTO cartoes
    (id_cartao, saldo, ativo, pin_hash)
    VALUES (?, ?, ?, ?)
""", (
    "123456",
    10000,
    1,
    generate_password_hash("1234")
))

conexao.commit()
conexao.close()

print("Cartão fictício cadastrado com sucesso!")
print("ID: 123456")
print("Saldo: R$ 100,00")
