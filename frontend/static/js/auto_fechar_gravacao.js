/* =========================================================
   PROJETO: Orion
   PASTA: C:\orion\frontend\static\js
   MODULO: static\js\auto_fechar_gravacao.js
   AUTOR: Benedito Silva Filho
   CRIADO EM: 2026-10-17 12:55 -03
   ATUALIZADO EM: 2026-10-26 17:00 -03
   VERSAO: 1.1.0

   DESCRICAO:
     Peca unica (Sessao 099): a mensagem "Gravacao Efetuada com Sucesso" fecha
     sozinha depois de alguns segundos (padrao 3), para o usuario nao precisar
     clicar. Mostra a contagem no botao ("Sair (3)", "Sair (2)"...). Se o usuario
     clicar em Sair ou apertar Enter antes, a tela faz o que sempre fez e a
     contagem para. Ao zerar, o script CLICA no botao Sair, entao tudo o que o
     botao ja faz (voltar o foco, ir para a Selecao quando a GTA encerra) acontece
     igual.
     NAO mexe na regra de abrir/fechar a mensagem: so observa a classe "aberto"
     do modal. Uso (no fim da pagina, depois do script da tela):
       <script src="/static/js/auto_fechar_gravacao.js"></script>
       <script>AutoFecharGravacao.iniciar({ modal: 'modal-sucesso', botao: 'btn-modal-sair', segundos: 3 });</script>
     Nunca escrever um relogio proprio de fechamento em tela nenhuma.

     v1.0.0: Criacao (Sessao 099).
     v1.1.0: Sessao 106 (26/10/2026, 17:00 -03) - o modal pode pedir mais tempo com o atributo data-segundos (lido a cada abertura; sem o
             atributo vale o padrao). Usado na mensagem de GTA COMPLETA da Brincagem (texto longo). REVERSAO: .bak_antes_s106r.
   ========================================================= */
(function () {
    'use strict';

    function iniciar(opcoes) {
        opcoes = opcoes || {};
        var modal = document.getElementById(opcoes.modal || 'modal-sucesso');
        var botao = document.getElementById(opcoes.botao || 'btn-modal-sair');
        if (!modal || !botao) { return; }
        var segundos = parseInt(opcoes.segundos, 10) || 3;
        var rotuloOriginal = botao.textContent;
        var relogio = null;

        // Para a contagem e devolve o texto original do botao.
        function parar() {
            if (relogio !== null) { clearInterval(relogio); relogio = null; }
            botao.textContent = rotuloOriginal;
        }

        // Comeca a contagem regressiva; ao zerar, confirma sozinho (clica em Sair).
        function comecar() {
            parar();
            var restante = parseInt(modal.getAttribute('data-segundos'), 10) || segundos;   // v1.1.0
            botao.textContent = rotuloOriginal + ' (' + restante + ')';
            relogio = setInterval(function () {
                restante -= 1;
                if (restante <= 0) {
                    parar();
                    botao.click();
                    return;
                }
                botao.textContent = rotuloOriginal + ' (' + restante + ')';
            }, 1000);
        }

        // Observa so a classe do modal: abriu -> conta; fechou (por qualquer caminho) -> para.
        new MutationObserver(function () {
            if (modal.classList.contains('aberto')) {
                if (relogio === null) { comecar(); }
            } else {
                parar();
            }
        }).observe(modal, { attributes: true, attributeFilter: ['class'] });
    }

    window.AutoFecharGravacao = { iniciar: iniciar };
})();
/* =========================================================
   FIM DE ARQUIVO: static\js\auto_fechar_gravacao.js
   ========================================================= */
