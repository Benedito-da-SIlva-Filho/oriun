<!--
  Componente: CabecalhoConsiste.svelte
  Descrição: Cabeçalho institucional da Consiste Informática.
  Exibe o logotipo da empresa em largura total, ocupando todo o topo da página.
  A imagem está hospedada externamente via Postimages.
  O layout é responsivo, adaptado para desktop e dispositivos móveis.
-->

<script>
  // Nenhuma lógica JS necessária neste componente visual
</script>

<!-- Estrutura visual do cabeçalho -->
<div class="cabecalho">
  <img
    src="https://i.postimg.cc/k5MqWRhd/Cabec.png"
    alt="Logotipo da Consiste Informática"
    class="logo-topo"
  />
</div>

<style>
  .cabecalho {
    width: 100%;
    background-color: #fff;
    border-bottom: 2px solid #e65c00;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 16px 0;
    box-sizing: border-box;
  }

  .logo-topo {
    width: 100%;
    max-height: 140px;
    object-fit: cover;
    display: block;
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  }

  @media (max-width: 600px) {
    .logo-topo {
      max-height: 100px;
    }

    .cabecalho {
      padding: 12px 0;
    }
  }
</style>
