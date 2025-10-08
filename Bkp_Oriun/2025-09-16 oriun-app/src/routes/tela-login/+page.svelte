<!--
  Componente: TelaLogin.svelte
  Descrição: Página de login do Sistema de Rastreabilidade Bovina (ORIUN),
  produto da Consiste Informática. Estrutura modular com cabeçalho separado.
  Layout responsivo com moldura institucional visível e simétrica em todos os dispositivos.
  Inclui campos de ID, senha, checkbox "Lembrar-me" e botão de login.
-->

<script>
  import CabecalhoConsiste from '$lib/components/CabecalhoConsiste.svelte';

  // Variáveis reativas vinculadas aos campos do formulário
  let id = '';
  let senha = '';
  let lembrarMe = false;

  // Função chamada ao clicar no botão "ENTRAR"
  function handleSubmit() {
    console.log('ID:', id);
    console.log('Senha:', senha);
    console.log('Lembrar-me:', lembrarMe);
    // Aqui você pode integrar com lógica de autenticação ou redirecionamento
  }
</script>

<style>
  .container {
    width: calc(100% - 32px); /* Garante espaço lateral para bordas */
    max-width: 720px;
    margin: 32px auto;
    padding: 32px;
    font-family: 'Segoe UI', sans-serif;
    background-color: #fff;
    border-left: 6px solid #e65c00;
    border-right: 6px solid #e65c00;
    border-radius: 12px;
    box-shadow: 0 0 16px rgba(0, 0, 0, 0.08);
    box-sizing: border-box;
    overflow-x: hidden;
  }

  .top-banner {
    height: 6px;
    background: linear-gradient(to right, #e65c00, #ff944d);
    border-radius: 4px;
    margin-bottom: 24px;
  }

  .oriun-logo {
    display: flex;
    justify-content: center;
    margin-bottom: 24px;
  }

  .oriun-logo img {
    max-height: 100px; /* Aumentado para dar mais destaque */
    width: auto;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  }

  .welcome-text {
    text-align: center;
    margin-bottom: 10px;
    font-size: 20px;
    font-weight: 600;
    color: #333;
  }

  .system-title {
    text-align: center;
    margin-bottom: 10px;
    font-size: 18px;
    font-weight: 500;
    color: #444;
  }

  .login-section {
    margin-top: 32px;
  }

  .login-section p {
    font-weight: bold;
    margin-bottom: 20px;
    font-size: 18px;
    color: #444;
    text-align: center;
  }

  label {
    display: block;
    margin-bottom: 6px;
    font-weight: bold;
    font-size: 14px;
  }

  input[type="text"],
  input[type="password"] {
    width: 100%;
    padding: 10px;
    margin-bottom: 16px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 15px;
  }

  .remember-me {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
  }

  .remember-me label {
    margin-left: 8px;
    font-weight: normal;
    font-size: 14px;
  }

  .btn-enter {
    background-color: #e65c00;
    color: white;
    padding: 12px;
    width: 100%;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .btn-enter:hover {
    background-color: #cc4f00;
  }

  .forgot-password {
    margin-top: 16px;
    font-size: 14px;
    text-align: center;
  }

  .forgot-password a {
    color: #e65c00;
    text-decoration: none;
  }

  .forgot-password a:hover {
    text-decoration: underline;
  }

  /* Borda adaptativa para telas menores */
  @media (max-width: 600px) {
    .container {
      width: calc(100% - 24px);
      margin: 16px auto;
      padding: 20px;
      border-left: 3px solid #e65c00;
      border-right: 3px solid #e65c00;
      border-radius: 8px;
      box-shadow: 0 0 8px rgba(0, 0, 0, 0.05);
    }

    .oriun-logo img {
      max-height: 80px; /* Aumentado proporcionalmente para mobile */
    }

    .welcome-text {
      font-size: 18px;
    }

    .system-title {
      font-size: 16px;
    }

    .login-section p {
      font-size: 17px;
    }

    .btn-enter {
      font-size: 15px;
      padding: 10px;
    }
  }
</style>

<div class="container">
  <!-- Cabeçalho institucional da Consiste TI -->
  <CabecalhoConsiste />

  <!-- Banner decorativo institucional -->
  <div class="top-banner"></div>

  <!-- Logo do sistema ORIUN -->
  <div class="oriun-logo">
    <img src="https://i.postimg.cc/kXPtFyrS/Oriun-logo.png" alt="Logo Oriun" />
  </div>

  <!-- Mensagem de boas-vindas -->
  <p class="welcome-text">Olá! Que bom ter você aqui!</p>
  <p class="system-title">Acesse o Sistema de Rastreabilidade Bovina</p>

  <!-- Formulário de login -->
  <div class="login-section">
    <p>Conecte-se</p>

    <label for="seu-id">Seu ID:</label>
    <input type="text" id="seu-id" bind:value={id} />

    <label for="sua-senha">Sua Senha:</label>
    <input type="password" id="sua-senha" bind:value={senha} />

    <div class="remember-me">
      <input type="checkbox" id="lembrar-me" bind:checked={lembrarMe} />
      <label for="lembrar-me">Lembrar-me</label>
    </div>

    <button class="btn-enter" on:click={handleSubmit}>ENTRAR</button>

    <p class="forgot-password">
      Esqueceu sua senha?
      <a href="/recuperar-senha">Clique aqui!</a>
    </p>
  </div>
</div>
