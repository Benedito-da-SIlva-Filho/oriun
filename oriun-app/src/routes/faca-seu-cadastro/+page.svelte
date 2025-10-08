<script>
  import CabecalhoConsiste from '$lib/components/CabecalhoConsiste.svelte';
  import Logo from '$lib/components/Logo.svelte';
  import { validarCPF } from '$lib/utils/cpf.js';
  import { aplicarMascaraCPF } from '$lib/utils/mascaras.js';

  let cpf = '';
  let telefone = '';
  let senha = '';
  let confirmarSenha = '';
  let cpfInvalido = false;
  let telefoneInvalido = false;
  let mostrarSenha = false;
  let mostrarConfirmarSenha = false;

  function aplicarMascaraTelefone(valor) {
    const numeros = valor.replace(/\D/g, '').slice(0, 12);
    const ddd = numeros.slice(0, 3);
    const parte1 = numeros.slice(3, 8);
    const parte2 = numeros.slice(8, 12);

    if (numeros.length <= 3) return ddd;
    if (numeros.length <= 8) return `(${ddd}) ${parte1}`;
    return `(${ddd}) ${parte1}-${parte2}`;
  }

  function validarTelefone(telefone) {
    const telefoneLimpo = telefone.replace(/\D/g, '');
    const ddd = telefoneLimpo.substring(0, 3);
    const numero = telefoneLimpo.substring(3);

    const dddValido = /^\d{3}$/.test(ddd) && !['000','001','002','003','004','005','006','007','008','009'].includes(ddd);
    const numeroValido = numero.length === 9;

    return dddValido && numeroValido;
  }

  function handleCadastro() {
    const cpfLimpo = cpf.replace(/\D/g, '');
    cpfInvalido = !validarCPF(cpfLimpo);
    telefoneInvalido = !validarTelefone(telefone);

    if (cpfInvalido) {
      alert('CPF incorreto. Por favor, verifique.');
      return;
    }

    if (telefoneInvalido) {
      alert('Telefone incorreto. Verifique o DDD e número.');
      return;
    }

    if (senha.length < 6) {
      alert('A senha deve ter pelo menos 6 caracteres.');
      return;
    }

    if (senha !== confirmarSenha) {
      alert('As senhas não coincidem.');
      return;
    }

    alert('Cadastro realizado com sucesso!');
    window.location.href = '/dashboard';
  }

  function validarCPFaoSair() {
    const cpfLimpo = cpf.replace(/\D/g, '');
    cpfInvalido = !validarCPF(cpfLimpo);
  }

  function validarTelefoneAoSair() {
    telefoneInvalido = !validarTelefone(telefone);
  }

  function limparCPFaoFocar() {
    if (cpfInvalido) {
      cpf = '';
      cpfInvalido = false;
    }
  }

  function limparTelefoneAoFocar() {
    if (telefoneInvalido) {
      telefone = '';
      telefoneInvalido = false;
    }
  }

  function alternarSenha() {
    mostrarSenha = !mostrarSenha;
  }

  function alternarConfirmarSenha() {
    mostrarConfirmarSenha = !mostrarConfirmarSenha;
  }
</script>

<style>
  .center-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: #f9f9f9;
    padding: 24px;
    box-sizing: border-box;
  }

  .container {
    width: 100%;
    max-width: 440px;
    padding: 24px;
    font-family: 'Segoe UI', sans-serif;
    
    background-color: #fff;
    border-left: 4px solid #e65c00;
    border-right: 4px solid #e65c00;
    border-radius: 10px;
    box-shadow: 0 0 12px rgba(0, 0, 0, 0.08);
    box-sizing: border-box;
  }

  .top-banner {
    height: 4px;
    background: linear-gradient(to right, #e65c00, #ff944d);
    border-radius: 2px;
    margin-bottom: 12px;
  }

  .oriun-logo {
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
  }

  .oriun-logo :global(img) {
    max-height: 80px;
    width: auto;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }

  .welcome-text,
  .system-title {
    text-align: center;
    margin-bottom: 6px;
    font-size: 16px;
    font-weight: 500;
    color: #333;
  }

  .cadastro-section {
    margin-top: 16px;
  }

  .cadastro-section p {
    font-weight: bold;
    margin-bottom: 8px;
    font-size: 15px;
    color: #444;
    text-align: center;
  }

  label {
    display: block;
    margin-bottom: 6px;
    font-weight: bold;
    font-size: 13px;
  }
  .cpf-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 6px;
  }

  .cpf-inline-error {
  color: #e65c00;
  font-size: 15px;
  font-weight: bold;
  }

  .telefone-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 6px;
}

.telefone-inline-error {
  color: #e65c00;
  font-size: 15px;
  font-weight: bold;
}


  .dica-inline {
    font-size: 12px;
    font-weight: normal;
    color: #777;
    margin-left: 6px;
    font-style: italic;
  }

  input[type="text"],
  input[type="password"] {
    width: 100%;
    padding: 6px;
    margin-bottom: 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 14px;
    box-sizing: border-box;
  }

  input::placeholder {
    color: #bbb;
    font-style: italic;
    font-size: 13px;
  }

  .senha-wrapper {
    position: relative;
  }

  .senha-wrapper input {
    padding-right: 36px;
  }

  .senha-wrapper button {
    position: absolute;
    right: 6px;
    top: 6px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
  }

  :global(.aviso-cpf),
  :global(.aviso-telefone) {
  color: #e65c00 !important;
  font-size: 15px;
  font-weight: bold;
  margin-top: -4px;
  margin-bottom: 10px;
  min-height: 16px;
}


  .btn-cadastrar {
    background-color: #e65c00;
    color: white;
    padding: 12px;
    width: 100%;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-size: 15px;
    cursor: pointer;
    transition: background-color 0.3s ease;
    margin-top: 10px;
  }

  .btn-cadastrar:hover {
    background-color: #cc4f00;
  }
</style>

<div class="center-wrapper">
  <div class="container">
    <CabecalhoConsiste />
    <div class="top-banner"></div>
    <div class="oriun-logo">
      <Logo size="80px" />
    </div>
    <p class="welcome-text">Olá, que bom ter você aqui</p>
    <p class="system-title">Cadastre-se no Sistema de Rastreabilidade Bovina</p>

    <div class="cadastro-section">
      <p>Preencha seus dados</p>
      
            <label for="cpf" class="cpf-label">
        CPF:
        {#if cpfInvalido}
          <span class="cpf-inline-error">CPF incorreto. Corrija antes de continuar.</span>
        {/if}
      </label>
      <input
        type="text"
        id="cpf"
        bind:value={cpf}
        on:input={() => cpf = aplicarMascaraCPF(cpf)}
        on:blur={validarCPFaoSair}
        on:focus={limparCPFaoFocar}
        placeholder="Campo obrigatório"
      />
          
      <label for="telefone" class="telefone-label">
          Fone:
          {#if telefoneInvalido}
            <span class="telefone-inline-error">Fone incorreto. Verifique DDD e número.</span>
          {/if}
      </label>
      <input
        type="text"
        id="telefone"
        bind:value={telefone}
        on:input={() => telefone = aplicarMascaraTelefone(telefone)}
        on:blur={validarTelefoneAoSair}
        on:focus={limparTelefoneAoFocar}
        maxlength="17"
        placeholder="Campo obrigatório"
      />
      
      <label for="senha">
        Senha: <span class="dica-inline">mínimo 6 caracteres, letras e números</span>
      </label>
      <div class="senha-wrapper">
        <input
          type={mostrarSenha ? 'text' : 'password'}
          id="senha"
          bind:value={senha}
          placeholder="Campo obrigatório"
        />
        <button
          type="button"
          on:click={alternarSenha}
          aria-label="Mostrar senha"
        >
          {#if mostrarSenha}
            👁️
          {:else}
            👁️‍🗨️
          {/if}
        </button>
      </div>

      <label for="confirmarSenha">Confirmar Senha:</label>
      <div class="senha-wrapper">
        <input
          type={mostrarConfirmarSenha ? 'text' : 'password'}
          id="confirmarSenha"
          bind:value={confirmarSenha}
          placeholder="Campo obrigatório"
        />
        <button
          type="button"
          on:click={alternarConfirmarSenha}
          aria-label="Mostrar confirmar senha"
        >
          {#if mostrarConfirmarSenha}
            👁️
          {:else}
             👁️‍🗨️
          {/if}
        </button>
      </div>

      <button class="btn-cadastrar" on:click={handleCadastro}>
        CONFIRMAR
      </button>
    </div> <!-- fim da .cadastro-section -->
  </div> <!-- fim da .container -->
</div> <!-- fim da .center-wrapper -->
