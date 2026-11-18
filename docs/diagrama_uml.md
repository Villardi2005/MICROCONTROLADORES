
# Diagrama UML - Maquininha de Cartão

## Diagrama de Sequência

Este diagrama representa a comunicação entre o cliente,
o Arduino, o servidor Flask e o banco de dados SQLite
durante o processamento de uma compra.

```mermaid
sequenceDiagram
    actor Cliente
    participant Arduino
    participant Flask
    participant SQLite

    Cliente->>Arduino: Informa cartão, valor e PIN
    Arduino->>Flask: Solicita pagamento
    Flask->>SQLite: Consulta cartão
    SQLite-->>Flask: Retorna saldo e dados

    Flask->>Flask: Valida cartão, PIN e saldo

    alt Pagamento aprovado
        Flask->>SQLite: Atualiza saldo
        Flask->>SQLite: Registra transação
        Flask-->>Arduino: Compra aprovada
    else Pagamento recusado
        Flask->>SQLite: Registra recusa
        Flask-->>Arduino: Compra recusada
    end

    Arduino-->>Cliente: Exibe resultado
```
