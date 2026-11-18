from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash
from decimal import Decimal, InvalidOperation
from banco import conectar, criar_tabelas

app = Flask(__name__)
criar_tabelas()


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "mensagem": "Servidor da maquininha funcionando!",
        "status": "online"
    })


@app.route("/api/transacoes", methods=["POST"])
def realizar_compra():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "status": "erro",
            "motivo": "JSON inválido"
        }), 400

    id_cartao = dados.get("id_cartao")
    pin = dados.get("pin")
    valor = dados.get("valor")
    id_terminal = dados.get("id_terminal")

    if not isinstance(id_terminal, str) or not id_terminal:
        return jsonify({
        "status": "erro",
        "motivo": "ID do terminal inválido"
    }), 400

    if not isinstance(id_cartao, str) or not id_cartao:
        return jsonify({
            "status": "erro",
            "motivo": "ID do cartão inválido"
        }), 400

    if not isinstance(pin, str):
        return jsonify({
            "status": "erro",
            "motivo": "PIN inválido"
        }), 400

    # Converte o valor em reais para centavos
    try:
        if isinstance(valor, bool) or not isinstance(
            valor, (int, float, str)
        ):
            raise ValueError()

        valor_decimal = Decimal(str(valor))

        if not valor_decimal.is_finite() or valor_decimal <= 0:
            raise ValueError()

        valor_centavos = valor_decimal * 100

        if valor_centavos != valor_centavos.to_integral_value():
            raise ValueError()

        valor = int(valor_centavos)

    except (InvalidOperation, ValueError, TypeError):
        return jsonify({
            "status": "erro",
            "motivo": "Valor inválido"
        }), 400

    conexao = conectar()

    try:
        conexao.execute("BEGIN IMMEDIATE")

        terminal = conexao.execute("""
            SELECT * FROM terminais
            WHERE id_terminal = ?
        """, (id_terminal,)).fetchone()

        cartao = conexao.execute("""
            SELECT * FROM cartoes
            WHERE id_cartao = ?
        """, (id_cartao,)).fetchone()

        # Verifica as condições para aprovar a compra
        if terminal is None:
            motivo = "Terminal não autorizado"
       
        elif not terminal["ativo"]:
            motivo = "Terminal inativo"

        elif cartao is None:
            motivo = "Cartão não encontrado"

        elif not cartao["ativo"]:
            motivo = "Cartão inativo"

        elif not check_password_hash(cartao["pin_hash"], pin):
            motivo = "PIN incorreto"

        elif cartao["saldo"] < valor:
            motivo = "Saldo insuficiente"

        else:
            motivo = None

        # Aprova ou recusa a compra
        if motivo is None:
            novo_saldo = cartao["saldo"] - valor

            conexao.execute("""
                UPDATE cartoes
                SET saldo = ?
                WHERE id_cartao = ?
            """, (novo_saldo, id_cartao))

            status = "aprovada"

        else:
            status = "recusada"

        # Registra a transação no banco
        cursor = conexao.execute("""
            INSERT INTO transacoes
            (id_cartao, valor, status, motivo)
            VALUES (?, ?, ?, ?)
        """, (id_cartao, valor, status, motivo))

        id_transacao = cursor.lastrowid

        conexao.commit()

        # Monta a resposta da API
        resposta = {
            "id_transacao": id_transacao,
            "status": status,
            "motivo": motivo,
            "valor": f"{valor / 100:.2f}"
        }

        if status == "aprovada":
            resposta["saldo_restante"] = (
                f"{novo_saldo / 100:.2f}"
            )

        return jsonify(resposta), 200

    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao processar compra")

        return jsonify({
            "status": "erro",
            "motivo": "Erro interno do servidor"
        }), 500

    finally:
        conexao.close()


@app.route("/api/transacoes", methods=["GET"])
def listar_transacoes():
    conexao = conectar()

    try:
        transacoes = conexao.execute("""
            SELECT id, id_cartao, valor, status,
                   motivo, data_hora
            FROM transacoes
            ORDER BY id DESC
        """).fetchall()

        resultado = []

        for transacao in transacoes:
            resultado.append({
                "id": transacao["id"],
                "id_cartao": transacao["id_cartao"],
                "valor": f"{transacao['valor'] / 100:.2f}",
                "status": transacao["status"],
                "motivo": transacao["motivo"],
                "data_hora": transacao["data_hora"]
            })

        return jsonify(resultado), 200

    finally:
        conexao.close()


@app.route("/api/resumo", methods=["GET"])
def resumo():
    conexao = conectar()

    try:
        dados = conexao.execute("""
            SELECT
                COUNT(*) AS total_transacoes,
                SUM(CASE WHEN status = 'aprovada'
                    THEN 1 ELSE 0 END) AS aprovadas,
                SUM(CASE WHEN status = 'recusada'
                    THEN 1 ELSE 0 END) AS recusadas,
                COALESCE(SUM(CASE
                    WHEN status = 'aprovada'
                    THEN valor ELSE 0 END), 0) AS total_vendido
            FROM transacoes
        """).fetchone()

        return jsonify({
            "total_transacoes": dados["total_transacoes"],
            "aprovadas": dados["aprovadas"],
            "recusadas": dados["recusadas"],
            "total_vendido": f"{dados['total_vendido'] / 100:.2f}"
        }), 200

    finally:
        conexao.close()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
