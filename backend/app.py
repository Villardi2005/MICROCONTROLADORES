
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

from banco import conectar, criar_tabelas

app = Flask(__name__)
criar_tabelas()


def valor_em_reais(centavos):
    return round(centavos / 100, 2)


def data_atual():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def formatar_data(data_hora):
    if not data_hora:
        return None

    try:
        data = datetime.fromisoformat(data_hora)

        # Datas antigas do SQLite estavam em UTC
        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)

        return data.isoformat(timespec="seconds")

    except ValueError:
        return data_hora


def padronizar_motivo(motivo):
    motivos = {
        "Saldo insuficiente": "saldo_insuficiente",
        "PIN incorreto": "pin_incorreto",
        "Cartão não encontrado": "cartao_invalido",
        "Cartão inativo": "cartao_invalido",
        "Terminal não autorizado": "terminal_bloqueado",
        "Terminal inativo": "terminal_bloqueado"
    }

    return motivos.get(motivo, motivo)


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "mensagem": "Servidor da maquininha segura funcionando!",
        "status": "online"
    })


@app.route("/api/transacoes", methods=["POST"])
def realizar_compra():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "status": "erro",
            "motivo_recusa": "json_invalido"
        }), 400

    id_terminal = dados.get("id_terminal")
    id_cartao = dados.get("id_cartao")
    pin = dados.get("pin")
    valor = dados.get("valor")

    if not isinstance(id_terminal, str) or not id_terminal.strip():
        return jsonify({
            "status": "erro",
            "motivo_recusa": "terminal_invalido"
        }), 400

    if not isinstance(id_cartao, str) or not id_cartao.strip():
        return jsonify({
            "status": "erro",
            "motivo_recusa": "cartao_invalido"
        }), 400

    if not isinstance(pin, str):
        return jsonify({
            "status": "erro",
            "motivo_recusa": "pin_invalido"
        }), 400

    # Recebe valor em reais e converte para centavos
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

        valor_centavos = int(valor_centavos)

    except (InvalidOperation, ValueError, TypeError):
        return jsonify({
            "status": "erro",
            "motivo_recusa": "valor_invalido"
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

        # Regras de autorizacao
        if terminal is None or not terminal["ativo"]:
            motivo_recusa = "terminal_bloqueado"

        elif cartao is None or not cartao["ativo"]:
            motivo_recusa = "cartao_invalido"

        elif not check_password_hash(cartao["pin_hash"], pin):
            motivo_recusa = "pin_incorreto"

        elif cartao["saldo"] < valor_centavos:
            motivo_recusa = "saldo_insuficiente"

        else:
            motivo_recusa = None

        if motivo_recusa is None:
            novo_saldo = cartao["saldo"] - valor_centavos

            conexao.execute("""
                UPDATE cartoes
                SET saldo = ?
                WHERE id_cartao = ?
            """, (novo_saldo, id_cartao))

            status = "aprovada"

        else:
            status = "recusada"

        data_hora = data_atual()

        # Registra a transacao
        cursor = conexao.execute("""
            INSERT INTO transacoes
            (id_terminal, id_cartao, valor, status, motivo, data_hora)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            id_terminal,
            id_cartao,
            valor_centavos,
            status,
            motivo_recusa,
            data_hora
        ))

        id_transacao = f"TX{cursor.lastrowid:04d}"

        conexao.commit()

        resposta = {
            "id_transacao": id_transacao,
            "id_terminal": id_terminal,
            "id_cartao": id_cartao,
            "valor": valor_em_reais(valor_centavos),
            "status": status,
            "data_hora": data_hora,
            "motivo_recusa": motivo_recusa
        }

        if status == "aprovada":
            resposta["saldo_restante"] = valor_em_reais(novo_saldo)

        return jsonify(resposta), 200

    except Exception:
        conexao.rollback()
        app.logger.exception("Erro ao processar compra")

        return jsonify({
            "status": "erro",
            "motivo_recusa": "erro_interno"
        }), 500

    finally:
        conexao.close()


@app.route("/api/transacoes", methods=["GET"])
def listar_transacoes():
    conexao = conectar()

    try:
        transacoes = conexao.execute("""
            SELECT id, id_terminal, id_cartao, valor,
                   status, motivo, data_hora
            FROM transacoes
            ORDER BY id DESC
        """).fetchall()

        resultado = []

        for transacao in transacoes:
            resultado.append({
                "id_transacao": f"TX{transacao['id']:04d}",
                "id_terminal": transacao["id_terminal"],
                "id_cartao": transacao["id_cartao"],
                "valor": valor_em_reais(transacao["valor"]),
                "status": transacao["status"],
                "data_hora": formatar_data(
                    transacao["data_hora"]
                ),
                "motivo_recusa": padronizar_motivo(
                    transacao["motivo"]
                )
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
            "total_vendido": valor_em_reais(
                dados["total_vendido"]
            ),
            "total_transacoes": dados["total_transacoes"],
            "transacoes_aprovadas": dados["aprovadas"],
            "transacoes_recusadas": dados["recusadas"]
        }), 200

    finally:
        conexao.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
