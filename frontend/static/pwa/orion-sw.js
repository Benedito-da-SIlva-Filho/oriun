/* =========================================================
   PROJETO: Orion
   PASTA: C:\orion\frontend\static\pwa
   MODULO: orion-sw.js
   AUTOR: Benedito Silva Filho
   CRIADO EM: 2026-11-26 17:10 -03
   ATUALIZADO EM: 2026-11-26 17:10 -03
   VERSAO: 1.0.0

   DESCRICAO:
       Service worker do aplicativo instalavel do Orion (PWA).
       E servido pelo app.py na rota /orion-sw.js (raiz do site),
       para valer em TODAS as telas.
       NAO guarda nada em cache: dado de animal, GTA e usuario
       sempre vem do servidor, nunca de copia velha. Serve so para
       o navegador oferecer "Instalar Orion".
       Se a internet cair, mostra uma mensagem simples em vez da
       tela de erro do navegador.

   CHANGELOG:
       v1.0.0 - 2026-11-26 17:10 -03 - Criacao do modulo (icone/aplicativo do Orion).
   ========================================================= */

// Instala e assume o controle na hora (sem esperar fechar as abas)
self.addEventListener('install', function (evento) {
    self.skipWaiting();
});

self.addEventListener('activate', function (evento) {
    evento.waitUntil(self.clients.claim());
});

// Navegacao (abrir tela): sempre pela rede. Sem internet: aviso simples.
// So mexe em GET de pagina; envio de formulario, upload e download seguem direto.
self.addEventListener('fetch', function (evento) {
    var pedido = evento.request;
    if (pedido.mode !== 'navigate' || pedido.method !== 'GET') {
        return;
    }
    evento.respondWith(
        fetch(pedido).catch(function () {
            return new Response(
                '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">' +
                '<meta name="viewport" content="width=device-width, initial-scale=1">' +
                '<title>Orion</title></head>' +
                '<body style="font-family:Arial,sans-serif;text-align:center;padding:48px 16px;color:#333">' +
                '<h2 style="color:#D4370A">Sem conexão</h2>' +
                '<p>O Orion precisa de internet. Confira a conexão e tente de novo.</p>' +
                '<p><a href="/" style="color:#D4370A">Tentar novamente</a></p>' +
                '</body></html>',
                { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
            );
        })
    );
});

/* =========================================================
   FIM DE ARQUIVO: orion-sw.js
   ========================================================= */
