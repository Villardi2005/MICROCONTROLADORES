
import json
import os
import sys

import requests
#import serial

URL_API = os.getenv(
    "URL_API",
    "http://127.0.0.1:5000/api/transacoes"
)

PORTA_SERIAL = os.getenv("PORTA_SERIAL", "/dev/ttyACM0")
VELOCIDADE = 9600


def processar_mensagem(mensagem):
    try:
        dados = json.loads(mensagem)

        resposta = requests.post(
            URL_API,
            json=dados,
            timeout=10
        )

        resposta.raise_for_status()
        return resposta.json()

    except json.JSONDecodeError:
        return {
            "status": "erro",
            "motivo": "JSON inválido"
        }

    except requests.RequestException:
        return {
            "status": "erro",
            "motivo": "Falha na comunicação com o servidor"
        }


def iniciar_serial():
    try:
        with serial.Serial(
            PORTA_SERIAL,
            VELOCIDADE,
            timeout=1
        ) as arduino:

            print("Aguardando mensagens do Arduino...")

            while True:
                linha = arduino.readline().decode(
                    "utf-8", errors="replace"
                ).strip()

                if linha:
                    print("Recebido:", linha)

                    resultado = processar_mensagem(linha)

                    arduino.write(
                        (json.dumps(resultado) + "\n").encode("utf-8")
                    )

                    print("Resposta:", resultado)

    except serial.SerialException as erro:
        print("Erro na comunicação serial:", erro)


def testar_simulacao():
    print("Modo de simulação ativado.")

    while True:
        try:
            mensagem = input(
                "Digite o JSON da compra (ou sair): "
            ).strip()

            if mensagem.lower() == "sair":
                break

            resultado = processar_mensagem(mensagem)
            print(json.dumps(resultado, ensure_ascii=False, indent=2))

        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    if "--simular" in sys.argv:
        testar_simulacao()
    else:
        iniciar_serial()
