# Демо

Окружение (один раз, из папки `report/`):

```
uv venv .venv
uv pip install -r requirements.txt
```

## Демо 1: ручной JSON-RPC

Скрипт играет роль редактора: запускает `pylsp`, шлёт ему `initialize` → `initialized` →
`didOpen` → `hover` → `shutdown` → `exit` и печатает каждое сообщение.

```
.venv/bin/python demo/demo1_raw_lsp.py --step
```

- `--step` — останавливаться на каждом шаге (Enter), удобно для выступления;
- `--full` — не сокращать длинные JSON;
- `--server "команда"` — подключить другой сервер вместо `pylsp`.

Файл, который «открывает» скрипт: `demo/sample.py` (в нём намеренно есть необъявленное имя,
чтобы сервер прислал диагностику).

## Демо 2: VS Code

Запускает отдельное окно VS Code с нашим мини-клиентом (`demo/vscode-ext/`) и отключёнными
остальными расширениями, чтобы Pylance не мешал: весь анализ делает `pylsp`.

```
demo/run_vscode.sh
```

Один раз нужно поставить зависимости клиента:

```
cd demo/vscode-ext && npm install
```

Что показать в `playground.py` (каждый запуск скрипта делает его свежей копией `sample.py`):

- волнистая линия под `undefined_name` — `textDocument/publishDiagnostics`;
- наведение на `area` — `textDocument/hover`;
- набрать `math.` — `textDocument/completion`;
- F12 на вызове `area(2)` — `textDocument/definition`;
- F2 на `area` — `textDocument/rename`;
- панель Output → «LSP Demo»: журнал JSON-RPC (`lspDemo.trace.server: verbose` задан в
  `demo/.vscode/settings.json`).

Настройки окна (светлая тема, крупный шрифт) лежат там же, в `demo/.vscode/settings.json`.
Другой сервер подключается изменением `lspDemo.serverCommand`.

## Демо 3: свой сервер

Тот же клиент в VS Code, но вместо `pylsp` запускается наш `mini/server.py` (около 80 строк
на `pygls`). Сервер ничего не знает о языке: работает с обычным текстом (`mini/notes.txt`,
каждый запуск скрипта делает свежую копию `mini/notes.sample.txt`).

```
demo/run_vscode.sh mini
```

Что показать:

- открыть `server.py`: весь сервер на виду, три обработчика (`didOpen/didChange`, `hover`, `completion`);
- жёлтое подчёркивание под `TODO` и красное под `FIXME` — `textDocument/publishDiagnostics`;
- `TODO` после эмодзи подчёркнут точно: функция `utf16()` переводит символы Python в единицы UTF-16;
- наведение на любое слово, в том числе русское — `textDocument/hover` (статистика слова);
- набрать новую строку и вызвать список (Ctrl+Space) — `textDocument/completion`;
- Output → «LSP Demo»: те же JSON-RPC сообщения, что и у `pylsp`.

Настройки окна лежат в `mini/.vscode/settings.json` (`lspDemo.languages` задаёт, для каких
файлов включать сервер). Stderr сервера пишется в `mini/server.log`.

Логи сервера (предупреждения `pylsp`, вывод `black`) уходят в `demo/pylsp.log`, а не в Output. Если что-то
не работает, смотреть нужно туда.
