/* =========================================================
   PROJETO: Orion
   PASTA: C:\orion\frontend\static\js
   MODULO: orion_mobile.js
   AUTOR: Benedito Silva Filho
   CRIADO EM: 2026-11-19 11:00 -03
   ATUALIZADO EM: 2026-11-19 11:00 -03
   VERSAO: 1.0.0

   DESCRICAO:
       Par do orion_mobile.css. No celular (ate 768px):
       - o menu lateral comeca ESCONDIDO (recebe a classe "recolhido");
       - ao abrir, aparece um fundo escuro; tocar no fundo fecha a gaveta.
       Em tela grande nao faz nada. Usa o toggleMenu() que cada tela ja tem.
       v1.0.0: Criacao do modulo (Sessao 133).
   ========================================================= */
(function () {
    function iniciar() {
        var sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
        if (!sidebar) { return; }
        var fundo = document.createElement('div');
        fundo.className = 'orion-gaveta-fundo';
        document.body.appendChild(fundo);
        function celular() { return window.matchMedia('(max-width: 768px)').matches; }
        function atualizar() {
            if (celular() && !sidebar.classList.contains('recolhido')) { fundo.classList.add('aberta'); }
            else { fundo.classList.remove('aberta'); }
        }
        if (celular()) { sidebar.classList.add('recolhido'); }
        new MutationObserver(atualizar).observe(sidebar, { attributes: true, attributeFilter: ['class'] });
        fundo.addEventListener('click', function () { sidebar.classList.add('recolhido'); });
        window.addEventListener('resize', atualizar);
        atualizar();
    }
    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', iniciar); }
    else { iniciar(); }
})();
/* =========================================================
   FIM DE ARQUIVO: orion_mobile.js
   ========================================================= */
