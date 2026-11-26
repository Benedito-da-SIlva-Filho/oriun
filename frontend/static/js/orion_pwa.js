/* =========================================================
   PROJETO: Orion
   PASTA: C:\orion\frontend\static\js
   MODULO: orion_pwa.js
   AUTOR: Benedito Silva Filho
   CRIADO EM: 2026-11-26 17:10 -03
   ATUALIZADO EM: 2026-11-26 17:10 -03
   VERSAO: 1.0.0

   DESCRICAO:
       Registra o service worker (/orion-sw.js) para o navegador
       oferecer "Instalar Orion" (aplicativo com icone proprio).
       Injetado pelo app.py (_injetar_mobile) em TODAS as telas
       HTML, sem mexer nos templates. So age em HTTPS (ou localhost);
       qualquer falha e ignorada e nunca atrapalha a tela.

   CHANGELOG:
       v1.0.0 - 2026-11-26 17:10 -03 - Criacao do modulo (icone/aplicativo do Orion).
   ========================================================= */
(function () {
    'use strict';
    try {
        if (!('serviceWorker' in navigator)) { return; }
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/orion-sw.js', { scope: '/' }).catch(function () {
                /* sem service worker o Orion funciona igual; so nao oferece instalar */
            });
        });
    } catch (erro) {
        /* nunca derruba a tela por causa do aplicativo instalavel */
    }
})();

/* =========================================================
   FIM DE ARQUIVO: orion_pwa.js
   ========================================================= */
