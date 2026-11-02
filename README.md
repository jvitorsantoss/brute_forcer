# brute_forcer

Ferramenta de brute force de login em serviços de rede, escrita em Python.
Feita para estudo de pentest (Solyd).

> ⚠️ **Uso autorizado apenas.** Use somente contra alvos para os quais você
> tem permissão explícita por escrito (lab próprio, CTF, contrato de pentest).
> Brute force sem autorização é crime. A responsabilidade pelo uso é sua.

## Protocolos suportados

- `ssh`
- `ftp`
- `http-post` (formulário de login via POST)

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
# SSH, usuario fixo, parando no primeiro acerto
python bruteforce.py ssh 10.0.0.5 -u admin -P senhas.txt

# FTP, lista de usuarios + lista de senhas
python bruteforce.py ftp 10.0.0.5 -U users.txt -P senhas.txt

# HTTP POST form
python bruteforce.py http-post alvo.lab -u admin -P senhas.txt \
    --path /login --user-field username --pass-field password \
    --fail-text "usuário ou senha inválidos"
```

### Opções úteis

| flag | descrição |
|------|-----------|
| `-u / --user` | usuário único |
| `-U / --userlist` | arquivo com usuários (um por linha) |
| `-P / --passlist` | arquivo com senhas (obrigatório) |
| `-t / --threads` | número de threads (default 8) |
| `--delay` | atraso por tentativa, em segundos (evita rate limit) |
| `--timeout` | timeout de conexão (default 8s) |
| `--all` | não parar no primeiro sucesso |
| `-p / --port` | porta (default por protocolo) |

Para `http-post`, o sucesso é detectado pela **ausência** do texto passado em
`--fail-text` na resposta. Ajuste conforme a aplicação alvo.

## Estrutura

```
brute_forcer/
├── bruteforce.py          # CLI + engine
├── requirements.txt
└── README.md
```
