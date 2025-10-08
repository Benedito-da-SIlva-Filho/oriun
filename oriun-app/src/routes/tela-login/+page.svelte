<!--
  Componente: TelaLogin.svelte
  Descrição: Página de login do Sistema de Rastreabilidade Bovina (ORIUN),
  produto da Consiste Informática. Layout institucional compacto e centralizado,
  com moldura simétrica, integração com backend FastAPI via fetch.
  Armazena token e redireciona para /dashboard.
  Inclui link para recuperação de senha e cadastro de novos usuários.
-->

<script>
  import CabecalhoConsiste from '$lib/components/CabecalhoConsiste.svelte';

  let id = '';
  let senha = '';
  let lembrarMe = false;

  async function handleSubmit() {
    try {
      const response = await fetch('http://127.0.0.1:8000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: id,
          password: senha
        })
      });

      const data = await response.json();

      if (data.token) {
        console.log('Login bem-sucedido! Token:', data.token);
        lembrarMe
          ? localStorage.setItem('oriun_token', data.token)
          : sessionStorage.setItem('oriun_token', data.token);
        window.location.href = '/dashboard';
      } else {
        alert('Credenciais inválidas. Tente novamente.');
      }
    } catch (error) {
      console.error('Erro ao conectar com o servidor:', error);
      alert('Erro de conexão. Verifique se o backend está rodando.');
    }
  }
</script>

<style>
  .center-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: #f9f9f9;
    padding: 16px;
    box-sizing: border-box;
  }

  .container {
    width: 100%;
    max-width: 420px;
    padding: 20px;
    font-family: 'Segoe UI', sans-serif;
    background-color: #fff;
    border-left: 4px solid #e65c00;
    border-right: 4px solid #e65c00;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.06);
    box-sizing: border-box;
  }

  .top-banner {
    height: 4px;
    background: linear-gradient(to right, #e65c00, #ff944d);
    border-radius: 2px;
    margin-bottom: 16px;
  }

  .oriun-logo {
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
  }

  .oriun-logo img {
    max-height: 90px;
    width: auto;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  }

  .welcome-text {
    text-align: center;
    margin-bottom: 6px;
    font-size: 16px;
    font-weight: 600;
    color: #333;
  }

  .system-title {
    text-align: center;
    margin-bottom: 6px;
    font-size: 15px;
    font-weight: 500;
    color: #444;
  }

  .login-section {
    margin-top: 20px;
  }

  .login-section p {
    font-weight: bold;
    margin-bottom: 14px;
    font-size: 16px;
    color: #444;
    text-align: center;
  }

  label {
    display: block;
    margin-bottom: 4px;
    font-weight: bold;
    font-size: 13px;
  }

  input[type="text"],
  input[type="password"] {
    width: 100%;
    padding: 8px;
    margin-bottom: 12px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 14px;
    box-sizing: border-box;
  }

  .remember-me {
    display: flex;
    align-items: center;
    margin-bottom: 14px;
  }

  .remember-me label {
    margin-left: 8px;
    font-weight: normal;
    font-size: 13px;
  }

  .btn-enter {
    background-color: #e65c00;
    color: white;
    padding: 10px;
    width: 100%;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .btn-enter:hover {
    background-color: #cc4f00;
  }

  .forgot-password,
  .cadastro-link {
    margin-top: 12px;
    font-size: 13px;
    text-align: center;
  }

  .forgot-password a,
  .cadastro-link a {
    color: #e65c00;
    text-decoration: none;
    font-weight: bold;
  }

  .forgot-password a:hover,
  .cadastro-link a:hover {
    text-decoration: underline;
  }
</style>

<div class="center-wrapper">
  <div class="container">
    <CabecalhoConsiste />
    <div class="top-banner"></div>
    <div class="oriun-logo">
      <img src="/logo-oriun.png" alt="Logo Oriun" />
    </div>
    <p class="welcome-text">Olá! Que bom ter você aqui!</p>
    <p class="system-title">Acesse o Sistema de Rastreabilidade Bovina</p>

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

      <p class="cadastro-link">
        Faça o seu Cadastro?
        <a href="/faca-seu-cadastro">Clique aqui!</a>
      </p>
    </div>
  </div>
</div>
