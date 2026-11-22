
function formatarValor(valor) {
    return Number(valor).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

async function carregarResumo() {
    const resposta = await fetch("/api/resumo");
    const dados = await resposta.json();

    document.getElementById("total_vendido").textContent =
        formatarValor(dados.total_vendido);

    document.getElementById("total_transacoes").textContent =
        dados.total_transacoes;

    document.getElementById("aprovadas").textContent =
        dados.transacoes_aprovadas;

    document.getElementById("recusadas").textContent =
        dados.transacoes_recusadas;
}

async function carregarTransacoes() {
    const resposta = await fetch("/api/transacoes");
    const transacoes = await resposta.json();

    const tabela = document.getElementById("tabela_transacoes");
    tabela.innerHTML = "";

    let totalAprovado = 0;
    let totalRecusado = 0;

    transacoes.forEach(function(transacao) {
        const linha = document.createElement("tr");

        const valores = [
            transacao.id_transacao,
            transacao.id_terminal,
            formatarValor(transacao.valor),
            transacao.status,
            transacao.data_hora
                ? new Date(transacao.data_hora).toLocaleString("pt-BR")
                : "-"
        ];

        valores.forEach(function(valor) {
            const coluna = document.createElement("td");
            coluna.textContent = valor;
            linha.appendChild(coluna);
        });

        tabela.appendChild(linha);

        if (transacao.status === "aprovada") {
            totalAprovado += transacao.valor;
        } else if (transacao.status === "recusada") {
            totalRecusado += transacao.valor;
        }
    });

    criarGrafico(totalAprovado, totalRecusado);
}

function criarGrafico(aprovado, recusado) {
    const grafico = document.getElementById("grafico");
    grafico.innerHTML = "";

    const maior = Math.max(aprovado, recusado, 1);

    [aprovado, recusado].forEach(function(valor, indice) {
        const grupo = document.createElement("div");

        const barra = document.createElement("div");
        barra.className = "barra";
        barra.style.height = (valor / maior * 130) + "px";

        const legenda = document.createElement("p");
        legenda.textContent = indice === 0 ? "Aprovadas" : "Recusadas";

        grupo.appendChild(barra);
        grupo.appendChild(legenda);
        grafico.appendChild(grupo);
    });
}

async function atualizarDashboard() {
    try {
        await carregarResumo();
        await carregarTransacoes();
    } catch (erro) {
        console.error("Erro ao carregar dashboard:", erro);
    }
}

atualizarDashboard();
setInterval(atualizarDashboard, 5000);