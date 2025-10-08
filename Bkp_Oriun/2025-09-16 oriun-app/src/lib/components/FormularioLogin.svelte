<!--
  Componente: FormularioLogin.svelte
  Descrição: Tela de login institucional para o sistema ORIUN (Sistema de Rastreabilidade Bovina),
  produto da Consiste Informática. Layout refinado com identidade visual clara e responsiva.
-->

<script>
  let id = '';
  let senha = '';
  let lembrarMe = false;

  function handleSubmit() {
    console.log('ID:', id);
    console.log('Senha:', senha);
    console.log('Lembrar-me:', lembrarMe);
    // Aqui você pode integrar com lógica de autenticação ou redirecionamento
  }
</script>

<style>
  .container {
    max-width: 420px;
    margin: 0 auto;
    padding: 24px;
    font-family: Arial, sans-serif;
    background-color: #fff;
  }

  .consiste-header {
    text-align: center;
    font-size: 13px;
    color: #e65c00;
    margin-bottom: 10px;
  }

  .logo-oriun {
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
  }

  .logo-oriun img {
    max-height: 80px;
    width: auto;
  }

  .welcome-text,
  .system-title {
    text-align: center;
    margin-bottom: 8px;
    font-size: 16px;
    color: #333;
  }

  .login-section {
    margin-top: 24px;
  }

  .login-section p {
    font-weight: bold;
    margin-bottom: 16px;
    font-size: 15px;
    color: #444;
  }

  label {
    display: block;
    margin-bottom: 4px;
    font-weight: bold;
    font-size: 14px;
  }

  input[type="text"],
  input[type="password"] {
    width: 100%;
    padding: 8px;
    margin-bottom: 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .remember-me {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }

  .remember-me label {
    margin-left: 8px;
    font-weight: normal;
    font-size: 14px;
  }

  .btn-enter {
    background-color: #e65c00;
    color: white;
    padding: 10px;
    width: 100%;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .btn-enter:hover {
    background-color: #cc4f00;
  }

  .forgot-password {
    margin-top: 12px;
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
</style>

<div class="container">
  <!-- Cabeçalho institucional da Consiste TI -->
  <div class="consiste-header">
    Consiste Informática – www.consisteti.com.br
  </div>

  <!-- Logo do sistema ORIUN -->
  <div class="logo-oriun">
    <img src="/images/Oriun_logo.png" alt="Logo Oriun" />
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
      Esqueceu sua senha? <a href="#">Clique aqui!</a>
    </p>
  </div>
</div>
