#!/usr/bin/env python3
"""Демо 3: свой языковой сервер на pygls.

Умеет три вещи:
  - диагностика: подчёркивает TODO (предупреждение) и FIXME (ошибка);
  - hover: статистика слова под курсором;
  - completion: заготовки TODO: / FIXME: / NOTE:.

Про язык файла сервер ничего не знает: работает с любым текстом.
Запуск по stdio: в stdout нельзя печатать ничего, кроме сообщений протокола.
"""

import re

from lsprotocol import types
from pygls.lsp.server import LanguageServer

server = LanguageServer("todo-server", "v0.1")

MARKERS = {
    "TODO": types.DiagnosticSeverity.Warning,
    "FIXME": types.DiagnosticSeverity.Error,
}
MARKER_RE = re.compile(r"\b(" + "|".join(MARKERS) + r")\b")

# По умолчанию pygls считает словом только латиницу и цифры; нам нужна и кириллица
WORD_START = re.compile(r"\w*$")
WORD_END = re.compile(r"^\w*")


def utf16(line: str, index: int) -> int:
    """Смещение в строке в единицах UTF-16: так считает протокол по умолчанию.

    Для эмодзи в Python один символ, а в UTF-16 два, без этой функции
    подчёркивание после эмодзи съехало бы на один символ влево."""
    return len(line[:index].encode("utf-16-le")) // 2


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def check(ls: LanguageServer, params):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = []
    for number, line in enumerate(doc.lines):
        for match in MARKER_RE.finditer(line):
            diagnostics.append(
                types.Diagnostic(
                    range=types.Range(
                        start=types.Position(line=number, character=utf16(line, match.start())),
                        end=types.Position(line=number, character=utf16(line, match.end())),
                    ),
                    message=f"{match.group(1)}: незавершённое дело",
                    severity=MARKERS[match.group(1)],
                    source="todo-server",
                )
            )
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(uri=doc.uri, diagnostics=diagnostics)
    )


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: types.HoverParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    word = doc.word_at_position(params.position, WORD_START, WORD_END)
    if not word:
        return None
    count = len(re.findall(rf"\b{re.escape(word)}\b", doc.source))
    return types.Hover(contents=f"**{word}**: {len(word)} букв, встречается {count} раз")


@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: types.CompletionParams):
    return [
        types.CompletionItem(label=marker, detail="маркер", insert_text=f"{marker}: ")
        for marker in ("TODO", "FIXME", "NOTE")
    ]


if __name__ == "__main__":
    server.start_io()
