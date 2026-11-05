#!/usr/bin/env bash
# Запускает отдельное окно VS Code (Extension Development Host) с нашим мини-клиентом LSP.
# Остальные расширения отключены, чтобы Pylance не мешал: весь анализ делает pylsp.
#
# В окне открывается playground.py: каждый запуск это свежая копия sample.py,
# поэтому правки во время демо не портят sample.py (он нужен демо 1).
#
#   demo/run_vscode.sh        демо 2: pylsp и playground.py
#   demo/run_vscode.sh mini   демо 3: свой сервер mini/server.py и mini/notes.txt
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

if [ "${1:-}" = "mini" ]; then
  cp "$here/mini/notes.sample.txt" "$here/mini/notes.txt"
  exec code --disable-extensions --extensionDevelopmentPath="$here/vscode-ext" "$here/mini" "$here/mini/notes.txt" "$here/mini/server.py"
fi

cp "$here/sample.py" "$here/playground.py"
exec code --disable-extensions --extensionDevelopmentPath="$here/vscode-ext" "$here" "$here/playground.py"
