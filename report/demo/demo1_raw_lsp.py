#!/usr/bin/env python3
"""Демо 1: общаемся с языковым сервером вручную, по JSON-RPC.

Скрипт сам играет роль редактора (клиента LSP): запускает сервер как дочерний
процесс, шлёт ему сообщения через stdin и печатает всё, что приходит из stdout.

    python demo/demo1_raw_lsp.py            # прогнать сценарий целиком
    python demo/demo1_raw_lsp.py --step     # по нажатию Enter на каждом шаге
    python demo/demo1_raw_lsp.py --full     # не сокращать длинные JSON

Сервер по умолчанию: pylsp из текущего окружения. Другой сервер:
    python demo/demo1_raw_lsp.py --server "pyright-langserver --stdio"
"""

import argparse
import json
import os
import queue
import shlex
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "sample.py"

# Позиция для hover: строка 8 (с нуля) файла sample.py, символ внутри `area` в print(area(2)).
HOVER_POSITION = {"line": 8, "character": 8}

COLOR = sys.stdout.isatty()

# Объекты такого вида всегда пишем в одну строку: range, position
INLINE_KEYS = ({"line", "character"}, {"start", "end"})


def render(value, indent=0, max_depth=99, depth=0):
    """JSON с отступами, но мелкие объекты (позиции, диапазоны) и глубокие уровни - в одну строку."""
    one_line = json.dumps(value, ensure_ascii=False)
    if not isinstance(value, (dict, list)) or not value:
        return one_line
    if depth >= max_depth or (isinstance(value, dict) and set(value) in INLINE_KEYS):
        return one_line
    pad, inner = "  " * indent, "  " * (indent + 1)
    if isinstance(value, dict):
        items = [f"{inner}{json.dumps(k, ensure_ascii=False)}: {render(v, indent + 1, max_depth, depth + 1)}" for k, v in value.items()]
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"
    items = [f"{inner}{render(v, indent + 1, max_depth, depth + 1)}" for v in value]
    return "[\n" + ",\n".join(items) + f"\n{pad}]"


def paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if COLOR else text


class Connection:
    """Один сеанс обмена с сервером: отправка кадров и чтение ответов."""

    def __init__(self, command, max_lines, step):
        self.max_lines = max_lines
        self.step = step
        self.next_id = 0
        self.methods = {}  # id запроса -> имя метода, чтобы подписывать ответы
        self.inbox = queue.Queue()
        self.proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # логи сервера нам не нужны, stdout - только протокол
        )
        threading.Thread(target=self._read_loop, daemon=True).start()

    # ---------- чтение: разбираем кадры Content-Length ----------

    def _read_loop(self):
        out = self.proc.stdout
        while True:
            length = None
            while True:
                line = out.readline()
                if not line:
                    self.inbox.put(None)  # сервер закрыл stdout
                    return
                line = line.strip()
                if not line:
                    break  # пустая строка - конец заголовков
                name, _, value = line.decode("ascii").partition(":")
                if name.lower() == "content-length":
                    length = int(value)
            body = out.read(length)
            self.inbox.put((length, json.loads(body.decode("utf-8"))))

    # ---------- вывод ----------

    def _show(self, direction, length, msg):
        if "method" in msg and "id" in msg:
            kind = "запрос"
        elif "method" in msg:
            kind = "уведомление"
        else:
            kind = "ответ"
        name = msg.get("method") or f"({self.methods.get(msg.get('id'), '?')})"
        ident = f" #{msg['id']}" if "id" in msg else ""
        if direction == "out":
            title = paint(f"клиент → сервер   {kind}{ident} {name}", "1;34")
        else:
            title = paint(f"сервер → клиент   {kind}{ident} {name}", "1;33")
        print(f"\n{title}")
        print(paint(f"Content-Length: {length}", "2"))
        # ответ на initialize огромный: показываем capabilities по одной строке на возможность
        is_init = "method" not in msg and self.methods.get(msg.get("id")) == "initialize"
        lines = render(msg, max_depth=3 if is_init else 99).splitlines()
        if self.max_lines and len(lines) > self.max_lines:
            hidden = len(lines) - self.max_lines
            lines = lines[: self.max_lines] + [paint(f"  … ещё {hidden} строк (--full, чтобы показать всё)", "2")]
        print("\n".join(lines))

    def pause(self, text):
        print("\n" + paint(f"━━ {text}", "1"))
        if self.step:
            input(paint("   [Enter] — продолжить ", "2"))

    # ---------- отправка ----------

    def _send(self, msg):
        body = json.dumps(msg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        frame = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
        self.proc.stdin.write(frame)
        self.proc.stdin.flush()
        self._show("out", len(body), msg)

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def request(self, method, params=None, timeout=15):
        self.next_id += 1
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        self.methods[self.next_id] = method
        if params is not None:
            msg["params"] = params
        self._send(msg)
        return self._wait(lambda m: m.get("id") == msg["id"] and "method" not in m, timeout)

    # ---------- приём ----------

    def _wait(self, predicate, timeout):
        """Читаем сообщения, пока не придёт подходящее. Всё остальное тоже печатаем."""
        while True:
            try:
                item = self.inbox.get(timeout=timeout)
            except queue.Empty:
                print(paint("   (таймаут: сервер ничего не прислал)", "31"))
                return None
            if item is None:
                return None
            length, msg = item
            self._show("in", length, msg)
            if "method" in msg and "id" in msg:
                # запрос от сервера к клиенту: честно отвечаем «пусто», чтобы он не ждал
                self._send({"jsonrpc": "2.0", "id": msg["id"], "result": None})
            if predicate(msg):
                return msg

    def wait_for(self, method, timeout=8):
        return self._wait(lambda m: m.get("method") == method, timeout)

    def close(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            code = self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            code = "убит"
        print("\n" + paint(f"сервер завершился, код выхода: {code}", "1"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server", help="команда запуска сервера (по умолчанию: pylsp из текущего окружения)")
    parser.add_argument("--step", action="store_true", help="останавливаться перед каждым шагом")
    parser.add_argument("--full", action="store_true", help="печатать JSON целиком, без сокращений")
    parser.add_argument("--max-lines", type=int, default=34, help="сколько строк JSON показывать (по умолчанию 34)")
    args = parser.parse_args()

    command = shlex.split(args.server) if args.server else [sys.executable, "-m", "pylsp"]
    try:
        conn = Connection(command, 0 if args.full else args.max_lines, args.step)
    except FileNotFoundError:
        sys.exit(f"Не удалось запустить сервер: {command[0]!r} не найден")

    root_uri = HERE.as_uri()
    doc_uri = SAMPLE.as_uri()
    text = SAMPLE.read_text(encoding="utf-8")

    print(paint("JSON показан с отступами для чтения; по проводу тело идёт без пробелов, его длина - в Content-Length.", "2"))
    conn.pause("1. initialize: знакомимся, обмениваемся возможностями (capabilities)")
    conn.request(
        "initialize",
        {
            "processId": os.getpid(),
            "clientInfo": {"name": "demo1", "version": "0.1"},
            "rootUri": root_uri,
            "workspaceFolders": [{"uri": root_uri, "name": "demo"}],
            "capabilities": {
                "textDocument": {
                    "hover": {"contentFormat": ["markdown", "plaintext"]},
                    "publishDiagnostics": {},
                },
            },
        },
    )

    conn.pause("2. initialized: «принято, начинаем» (уведомление, ответа не будет)")
    conn.notify("initialized", {})

    conn.pause("3. didOpen: передаём серверу текст файла; он сам пришлёт диагностики")
    conn.notify(
        "textDocument/didOpen",
        {"textDocument": {"uri": doc_uri, "languageId": "python", "version": 1, "text": text}},
    )
    conn.wait_for("textDocument/publishDiagnostics")

    conn.pause("4. hover: что находится под курсором на строке 9, в слове area?")
    conn.request(
        "textDocument/hover",
        {"textDocument": {"uri": doc_uri}, "position": HOVER_POSITION},
    )

    conn.pause("5. shutdown и exit: вежливо завершаем работу")
    conn.request("shutdown")
    conn.notify("exit")
    conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
