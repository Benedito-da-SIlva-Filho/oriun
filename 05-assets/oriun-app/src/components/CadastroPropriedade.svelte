<script>
  import { onMount } from 'svelte';

  let propriedade = {
    a001_Cod_Propriedade: '',
    a001_NIRF_INCRA: '',
    a001_Cod_Eras_Sisbov: '',
    a001_Inscr_Estadual: '',
    a001_Nome_Propriedade: '',
    a001_Endereco: '',
    a001_Municipio: '',
    a001_UF: '',
    a001_Cx_Postal: '',
    a001_Municipio_Proximo: '',
    a001_Distancia_Sede_Propriedade: '',
    a001_Area_Total: '',
    a001_Latitude: '',
    a001_Longitude: '',
    a001_Roteiro_propriedade: '',
    a001_Data_Cadastro: ''
  };

  onMount(() => {
    propriedade.a001_Data_Cadastro = new Date().toISOString().split('T')[0];
  });

  function cadastrarPropriedade() {
    localStorage.setItem('propriedade', JSON.stringify(propriedade));
    alert('Propriedade cadastrada com sucesso!');
  }
</script>

<h1>Cadastro de Propriedade</h1>

<section class="form-section">
  <h2>Dados da Propriedade</h2>
  <div class="grid-tripla">
    <input class="codigo" bind:value={propriedade.a001_Cod_Propriedade} disabled maxlength="7" />
    <input placeholder="NIRF / INCRA" bind:value={propriedade.a001_NIRF_INCRA} />
    <input placeholder="Código ERAS / SISBOV" bind:value={propriedade.a001_Cod_Eras_Sisbov} />
  </div>
  <div class="grid">
    <input placeholder="Nome da propriedade" bind:value={propriedade.a001_Nome_Propriedade} />
  </div>
</section>

<section class="form-section">
  <h2>Localização</h2>
  <div class="grid">
    <input class="campo-endereco" placeholder="Endereço" bind:value={propriedade.a001_Endereco} />
  </div>
  <div class="linha-municipio-uf-caixa">
    <input placeholder="Município" bind:value={propriedade.a001_Municipio} />
    <input placeholder="UF" bind:value={propriedade.a001_UF} maxlength="2" />
    <input placeholder="Caixa Postal" bind:value={propriedade.a001_Cx_Postal} maxlength="10" />
  </div>
  <div class="linha-municipio-proximo-distancia">
    <input class="campo-municipio-proximo" placeholder="Município mais próximo" bind:value={propriedade.a001_Municipio_Proximo} />
    <input class="campo-distancia" placeholder="Distância Município até a sede (km)" bind:value={propriedade.a001_Distancia_Sede_Propriedade} />
  </div>
</section>

<section class="form-section">
  <h2>Área e Geolocalização</h2>
  <div class="grid">
    <input placeholder="Área total (ha)" bind:value={propriedade.a001_Area_Total} />
    <input placeholder="Latitude" bind:value={propriedade.a001_Latitude} />
    <input placeholder="Longitude" bind:value={propriedade.a001_Longitude} />
  </div>
</section>

<section class="form-section">
  <h2>Roteiro de Acesso</h2>
  <div class="grid">
    <textarea class="roteiro" placeholder="Descreva como chegar à propriedade" bind:value={propriedade.a001_Roteiro_propriedade}></textarea>
  </div>
</section>

<div class="actions">
  <button on:click={cadastrarPropriedade}>Cadastrar</button>
</div>

<style>
  h1 {
    text-align: center;
    margin-top: 0.25rem;
    font-size: 1.6rem;
    color: #333;
  }

  .form-section {
    margin: 1rem auto;
    max-width: 900px;
    padding: 0 1rem;
  }

  .form-section h2 {
    font-size: 1.05rem;
    margin-top: 0.25rem;
    margin-bottom: 0.1rem;
    color: #444;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.1rem;
  }

  input,
  textarea {
    width: 100%;
    padding: 0.25rem 0.5rem;
    font-size: 1rem;
    border: 1px solid #ccc;
    border-radius: 6px;
    margin-bottom: 0.1rem;
    box-sizing: border-box;
    text-align: center;
  }

  textarea.roteiro {
    min-height: 6rem;
    resize: vertical;
    text-align: left;
  }

  .grid,
  .grid-tripla,
  .linha-municipio-uf-caixa,
  .linha-municipio-proximo-distancia {
    display: grid;
    gap: 0.2rem;
    margin-bottom: 0.1rem;
  }

  .grid-tripla {
    grid-template-columns: 80px 1fr 1fr;
  }

  .grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }

  .linha-municipio-uf-caixa {
    grid-template-columns: 2fr 0.5fr 1fr;
  }

  .linha-municipio-proximo-distancia {
    grid-template-columns: 2fr 1.6fr;
  }

  .campo-endereco {
    grid-column: 1 / -1;
    width: 100%;
  }

  .campo-municipio-proximo,
  .campo-distancia {
    width: 100%;
    text-align: center;
    padding-top: 0.25rem;
    padding-bottom: 0.25rem;
    font-size: 1rem;
    border: 1px solid #ccc;
    border-radius: 6px;
    box-sizing: border-box;
  }

  .actions {
    text-align: center;
    margin-top: 1rem;
  }

  button {
    background-color: #007bff;
    color: white;
    padding: 0.4rem 2rem;
    font-size: 1rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
  }

  button:hover {
    background-color: #0056b3;
  }

  @media (max-width: 600px) {
    .grid,
    .grid-tripla {
      grid-template-columns: 1fr;
    }

    input,
    textarea,
    button {
      font-size: 0.95rem;
      padding: 0.4rem;
    }

    .form-section {
      margin: 0.5rem;
      padding: 0;
    }
  }
</style>



