import { json } from '@sveltejs/kit';

export async function POST({ request }) {
  const body = await request.text();
  console.log("🛠️ Corpo recebido:", body);

  const { userId, password } = JSON.parse(body);
  console.log("🔐 Dados recebidos:", userId, password);

  if (userId === 'admin' && password === '1234') {
    return json({ success: true, user: { name: 'Administrador' } });
  }

  return json({ success: false }, { status: 401 });
}
