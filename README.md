# Maquininha Segura — Projeto de Microcontroladores

## 1. Sobre o projeto

Este projeto está sendo desenvolvido para a disciplina de Microcontroladores da PUC-Rio, com base em um desafio proposto em parceria com a Stone.

O objetivo é desenvolver uma maquininha de pagamentos simulados que, além de realizar transações, possua mecanismos de segurança para proteger os dados do cliente e identificar tentativas de violação do dispositivo.

O sistema é dividido em diferentes partes, incluindo firmware do Arduino, backend, banco de dados e dashboard.

Este README documenta principalmente o desenvolvimento do backend e do banco de dados.

## 2. Tecnologias utilizadas

- **Python:** linguagem utilizada no backend.
- **Flask:** criação da API de pagamentos.
- **SQLite:** armazenamento dos cartões, terminais e transações.
- **Werkzeug:** armazenamento seguro dos hashes dos PINs.
- **Requests:** comunicação HTTP entre a simulação e o servidor.
- **PySerial:** biblioteca prevista para a comunicação serial com o Arduino.
- **GitHub:** versionamento e compartilhamento do código.

## 3. Estrutura do backend

```text
MICROCONTROLADORES/
├── backend/
│   ├── app.py
│   ├── banco.py
│   ├── cadastrar_cartoes.py
│   ├── serial_bridge.py
│   └── requirements.txt
├── docs/
│   └── diagrama_uml.md
└── README.md
```

O banco de dados `maquininha.db` é gerado localmente e não é enviado ao GitHub.

## 4. Funcionalidades implementadas

### Cadastro de cartões fictícios

O sistema permite cadastrar cartões para simular pagamentos, armazenando:

- Identificador do cartão.
- Saldo disponível.
- Estado do cartão (ativo ou inativo).
- Hash do PIN.

### API de pagamentos

A API recebe as informações de uma compra e verifica:

1. Se o terminal está cadastrado e autorizado.
2. Se o cartão existe e está ativo.
3. Se o PIN informado está correto.
4. Se o cartão possui saldo suficiente.

Quando todas as verificações são aprovadas, o valor da compra é descontado do saldo e a transação é registrada.

Caso contrário, a compra é recusada e o motivo é registrado no banco.

### Autorização dos terminais

O sistema possui uma tabela de terminais cadastrados.

Um terminal desconhecido ou desativado não pode realizar pagamentos.

### Histórico e resumo

O backend permite consultar as transações realizadas, incluindo compras aprovadas e recusadas.

Também disponibiliza um resumo com a quantidade de transações, aprovações, recusas e o valor total aprovado.

## 5. Como executar o projeto

### Acessar a pasta do backend

```bash
cd backend
```

### Criar o ambiente virtual

```bash
python -m venv .venv
```

Ativar o ambiente no Linux ou Codespaces:

```bash
source .venv/bin/activate
```

### Instalar as dependências

```bash
pip install -r requirements.txt
```

### Criar o banco de dados

```bash
python banco.py
```

### Cadastrar o cartão de teste

```bash
python cadastrar_cartoes.py
```

O cartão utilizado nos testes possui:

- ID: `123456`
- PIN: `1234`
- Saldo inicial: R$ 100,00

Esses dados são exclusivamente fictícios e utilizados para demonstração.

### Cadastrar um terminal autorizado

```bash
python -c "from banco import conectar; c=conectar(); c.execute('INSERT OR IGNORE INTO terminais (id_terminal, nome, ativo) VALUES (?, ?, ?)', ('TERMINAL001', 'Maquininha Principal', 1)); c.commit(); c.close()"
```

### Iniciar o servidor Flask

```bash
python app.py
```

O servidor estará disponível, por padrão, em:

`http://127.0.0.1:5000`

## 6. Endpoints da API

| Método | Endpoint | Funcionalidade |
|---|---|---|
| GET | `/` | Verificar o funcionamento do servidor |
| POST | `/api/transacoes` | Processar pagamentos |
| GET | `/api/transacoes` | Consultar histórico |
| GET | `/api/resumo` | Consultar resumo das transações |

### Exemplo de pagamento

Requisição:

```json
{
  "id_terminal": "TERMINAL001",
  "id_cartao": "123456",
  "pin": "1234",
  "valor": 10.00
}
```

Exemplo de resposta para uma compra recusada:

```json
{
  "id_transacao": 10,
  "motivo": "Saldo insuficiente",
  "status": "recusada",
  "valor": "10.00"
}
```

O identificador da transação varia conforme o histórico do banco.

## 7. Simulação da comunicação com Arduino

Foi desenvolvido o arquivo `serial_bridge.py`, responsável por receber mensagens de pagamento e encaminhá-las à API Flask.

Atualmente, a comunicação pode ser testada sem o Arduino físico.

Com o Flask funcionando, execute em outro terminal:

```bash
python serial_bridge.py --simular
```

Digite uma mensagem JSON contendo o terminal, o cartão, o PIN e o valor da compra.

O programa enviará a solicitação ao servidor e mostrará a resposta.

A integração física com o Arduino será realizada em uma etapa posterior.

## 8. Testes realizados

Foram realizados testes de:

- Pagamento aprovado.
- Pagamento recusado por saldo insuficiente.
- PIN incorreto.
- Cartão inexistente.
- Terminal autorizado.
- Terminal desconhecido.
- Terminal desativado.
- Consulta ao histórico e ao resumo.
- Comunicação simulada entre Python e Flask.

Os testes confirmaram o funcionamento dessas funcionalidades no ambiente de desenvolvimento.

## 9. Segurança e próximas etapas

O backend já utiliza hash para verificar os PINs cadastrados e possui validação de terminais autorizados.

Entretanto, essas funcionalidades ainda não representam todos os mecanismos de segurança previstos para a Maquininha Segura.

Entre as funcionalidades previstas para etapas futuras estão:

- Registro de eventos de violação.
- Bloqueio de terminais após detecção de violação.
- Gerenciamento e renovação de chaves de segurança.
- Proteção das mensagens contra ataques de reenvio.
- Integração com os sensores do Arduino.
- Integração com o dashboard de monitoramento.

O projeto utiliza dados fictícios e não deve ser utilizado para processar pagamentos reais.

## 10. Diagrama UML

O diagrama de sequência do projeto está disponível em:

`docs/diagrama_uml.md`

Ele representa o fluxo de comunicação entre o cliente, o Arduino, o backend Flask e o banco de dados.

A comunicação física representada no diagrama corresponde à arquitetura planejada, ainda não integrada ao hardware.

## 11. Situação atual

O backend possui as principais funcionalidades de pagamento implementadas e testadas.

A API, o banco de dados, a autorização dos terminais, o histórico de transações e a comunicação simulada estão funcionando.

As próximas etapas envolvem o desenvolvimento dos mecanismos adicionais de segurança e a integração com os demais componentes do projeto.
