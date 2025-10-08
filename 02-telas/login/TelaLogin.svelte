<!--------------------------------------------------------------------------------------------------|
|  Tela de Login - ORIUM APP																	                                      |
|  Esta página permite ao usuário autenticar-se no sistema.									                 		    |
|  Estrutura baseada em boas práticas de acessibilidade, semântica e padronização.					        |
|																									                                                  |
|  ?? Guia rápido para iniciantes:																	                                |
|																									                                                  |
|  ? Como executar o projeto localmente:															                              |
|																									                                                  |
|  1. Abra o terminal na raiz do projeto (onde está o arquivo package.json).						            |
|  2. Instale as dependências com: npm install														                          |
|  3. Inicie o servidor com: npm run dev															                              |
|  4. Acesse no navegador: http://localhost:5173/tela-login											                    |
|																									                                                  |
|  ?? Se você renomear a pasta da rota, lembre-se de atualizar os links e redirecionamentos.	      |
|																									                                                  |
|  ?? Dica: Para tornar esta tela a página inicial, mova o conteúdo para src/routes/+page.svelte.	  |
|																									                                                  |
|  Este projeto segue boas práticas de acessibilidade, padronização de labels e organização modular.|
|  Sinta-se à vontade para explorar, aprender e contribuir!											                    |
|--------------------------------------------------------------------------------------------------->


<script>
  import { goto } from '$app/navigation';

  // Variáveis reativas para captura dos dados do formulário
  let usuarioId = '';
  let senhaUsuario = '';
  let lembrarUsuario = false;

  // Função de envio do formulário
  async function handleSubmit() {
    if (!usuarioId || !senhaUsuario) {
      alert('Por favor, preencha todos os campos.');
      return;
    }

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: usuarioId, senha: senhaUsuario })
      });

      const resultado = await response.json();

      if (resultado.success) {
        if (lembrarUsuario) {
          localStorage.setItem('usuario', JSON.stringify({ id: usuarioId }));
        }
        goto('/dashboard');
      } else {
        alert('ID ou senha inválidos.');
      }
    } catch (error) {
      console.error('Erro ao tentar login:', error);
      alert('Erro de conexão. Tente novamente mais tarde.');
    }
  }
</script>

<section class="login-container">
  <header>
    <img src="/logo.jpg" alt="Logo da Consiste Informática" class="logo" />
    <span class="site-url">www.consisteti.com.br</span>
  </header>

  <h2 class="saudacao">Olá! Que bom ter você aqui!</h2>

  <form on:submit|preventDefault={handleSubmit}>
    <label for="usuario-id">Seu ID:</label>
    <input
      id="usuario-id"
      bind:value={usuarioId}
      placeholder="Digite seu ID"
      aria-label="Campo de ID do usuário"
    />

    <label for="senha-usuario">Sua Senha:</label>
    <input
      type="password"
      id="senha-usuario"
      bind:value={senhaUsuario}
      placeholder="Digite sua senha"
      aria-label="Campo de senha do usuário"
    />

    <div class="remember-me" translate="no">
      <input
        type="checkbox"
        id="lembrar-usuario"
        bind:checked={lembrarUsuario}
      />
      <label for="lembrar-usuario" translate="no">Lembrar-me</label>
    </div>

    <button type="submit">Entrar</button>
    <a href="/recuperar-senha">Esqueceu sua senha? Clique aqui!</a>
  </form>
</section>

<style>
  /* Estilo global da tela de login */
  :root {
    color-scheme: light;
  }

  .login-container {
    max-width: 500px;
    margin: 0 auto;
    padding: 2rem;
    font-family: 'Open Sans', sans-serif;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .logo {
    width: 150px;
  }

  .site-url {
    font-size: 0.9rem;
    color: #666;
  }

  .saudacao {
    font-size: 1.5rem;
    font-weight: 600;
    color: #333;
    text-align: center;
    margin: 1rem 0;
    padding: 0.5rem;
    background-color: #f9f9f9;
    border-radius: 4px;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  input[type="text"],
  input[type="password"] {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .remember-me {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .remember-me label {
    white-space: nowrap;
    font-size: 1rem;
    font-weight: 500;
  }

  button {
    background-color: orange;
    color: white;
    padding: 0.75rem;
    border: none;
    font-weight: bold;
    cursor: pointer;
    border-radius: 4px;
  }

  a {
    font-size: 0.9rem;
    color: #555;
    text-decoration: underline;
    text-align: center;
    margin-top: 0.5rem;
  }
</style>
