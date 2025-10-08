<script>
  let userId = "";
  let password = "";
  let error = "";

  console.log("Enviando para o backend:", userId, password);

  async function handleSubmit(event) {
    event.preventDefault();
    console.log("Enviando para o backend:", userId, password);
    console.log("📤 Enviando:", userId, password);

    if (!userId || !password) {
      error = "Por favor, preencha o ID e a senha.";
      return;
    }

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ userId, password })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        window.location.href = "/dashboard";
      } else {
        error = "ID ou senha inválidos.";
      }
    } catch (err) {
      error = "Erro ao conectar com o servidor.";
      console.error(err);
    }
  }
</script>

<div class="max-w-sm mx-auto mt-10 p-6 bg-white rounded shadow">

  <!-- Logo da Consiste -->
  <img src="/logo_Consiste.jpg" alt="Consiste" class="mx-auto mb-4 w-32" />
    
  <h2 class="text-xl font-bold mb-4">Entrar Oriun</h2>

  {#if error}
    <p class="text-red-600 mb-4">{error}</p>
  {/if}

  <form on:submit={handleSubmit}>
    <label class="block mb-2">
      <span class="text-gray-700">ID do Usuário</span>
      <input
        type="text"
        bind:value={userId}
        class="mt-1 block w-full border rounded px-3 py-2"
        placeholder="Digite seu ID"
      />
    </label>

    <label class="block mb-4">
      <span class="text-gray-700">Senha</span>
      <input
        type="password"
        bind:value={password}
        class="mt-1 block w-full border rounded px-3 py-2"
        placeholder="Digite sua senha"
      />
    </label>

    <button
      type="submit"
      class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
    >
      Entrar
    </button>
  </form>
</div>
