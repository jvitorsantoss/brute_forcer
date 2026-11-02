"""
Site bobo pra testar brute force (estudo de pentest - Solyd).

Sobe um servidor local que imita o alvo do main.py:
  - GET  /admin/login.php  -> mostra o formulario de login
  - POST /admin/login.php  -> valida user/password

Se o login der certo, a resposta contem a palavra "logout"
(e eh isso que o main.py procura pra saber que achou a senha).

Uso:
    python server.py
Depois aponte o main.py para:
    http://localhost:8000/admin/login.php
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

# Credenciais corretas (a senha tambem esta no senha.txt)
USUARIO_CORRETO = "admin"
SENHA_CORRETA = "solyd123"

HOST = "localhost"
PORTA = 8000


PAGINA_LOGIN = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Painel Admin - Login</title>
  <style>
    body {{ font-family: sans-serif; background:#0f172a; color:#e2e8f0;
           display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }}
    .card {{ background:#1e293b; padding:32px; border-radius:12px; width:300px;
             box-shadow:0 10px 30px rgba(0,0,0,.4); }}
    h1 {{ font-size:18px; margin:0 0 20px; text-align:center; }}
    input {{ width:100%; padding:10px; margin:6px 0 14px; border:none;
             border-radius:6px; box-sizing:border-box; }}
    button {{ width:100%; padding:10px; border:none; border-radius:6px;
              background:#3b82f6; color:#fff; font-weight:bold; cursor:pointer; }}
    .msg {{ margin-bottom:14px; color:#f87171; font-size:13px; text-align:center; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Painel Administrativo</h1>
    {mensagem}
    <form method="POST" action="/admin/login.php">
      <input name="user" placeholder="Usuario" autocomplete="off">
      <input name="password" type="password" placeholder="Senha">
      <button type="submit">Entrar</button>
    </form>
  </div>
</body>
</html>
"""

PAGINA_SUCESSO = """<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Painel Admin</title></head>
<body style="font-family:sans-serif;background:#0f172a;color:#e2e8f0;padding:40px">
  <h1>Bem-vindo, admin!</h1>
  <p>Voce entrou no painel administrativo.</p>
  <a href="/admin/login.php" style="color:#3b82f6">logout</a>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _responder(self, html, status=200):
        corpo = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.startswith("/admin/login.php"):
            self._responder(PAGINA_LOGIN.format(mensagem=""))
        else:
            self._responder("<h1>404 - Nada aqui</h1>", status=404)

    def do_POST(self):
        if not self.path.startswith("/admin/login.php"):
            self._responder("<h1>404 - Nada aqui</h1>", status=404)
            return

        tamanho = int(self.headers.get("Content-Length", 0))
        dados = parse_qs(self.rfile.read(tamanho).decode("utf-8"))
        usuario = dados.get("user", [""])[0]
        senha = dados.get("password", [""])[0]

        if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
            # Resposta de sucesso contem "logout" -> main.py detecta aqui
            self._responder(PAGINA_SUCESSO)
        else:
            msg = '<div class="msg">Usuario ou senha incorretos.</div>'
            self._responder(PAGINA_LOGIN.format(mensagem=msg), status=401)

    def log_message(self, formato, *args):
        # deixa o log curtinho
        print(f"[req] {self.command} {self.path} -> {args[1]}")


if __name__ == "__main__":
    servidor = HTTPServer((HOST, PORTA), Handler)
    print(f"Alvo de estudo rodando em http://{HOST}:{PORTA}/admin/login.php")
    print(f"Login certo -> user: {USUARIO_CORRETO} | senha: {SENHA_CORRETA}")
    print("Ctrl+C pra parar.\n")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")
