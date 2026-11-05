// Минимальный клиент LSP для VS Code.
// Вся «магия» - класс LanguageClient из vscode-languageclient: он запускает сервер,
// говорит с ним по JSON-RPC и подключает ответы к возможностям редактора.
// Какой сервер запускать, берём из настройки lspDemo.serverCommand.

const path = require("path");
const vscode = require("vscode");
const { LanguageClient } = require("vscode-languageclient/node");

let client;

function activate() {
  const folder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? process.cwd();
  const config = vscode.workspace.getConfiguration("lspDemo");
  const [command, ...args] = config.get("serverCommand", []);
  const languages = config.get("languages", ["python"]);

  if (!command) {
    vscode.window.showWarningMessage("LSP Demo: задайте настройку lspDemo.serverCommand");
    return;
  }

  // Пути с «/» считаем от папки проекта, остальное (python, pylsp) ищется в PATH
  const resolved = command.includes("/") ? path.resolve(folder, command) : command;

  client = new LanguageClient(
    "lspDemo", // по этому id VS Code ищет настройку lspDemo.trace.server
    "LSP Demo",
    { command: resolved, args, options: { cwd: folder } }, // запуск по stdio
    { documentSelector: languages.map((language) => ({ scheme: "file", language })) },
  );

  client.start().then(
    () => vscode.window.setStatusBarMessage(`LSP Demo: сервер запущен (${path.basename(resolved)})`, 5000),
    (err) => vscode.window.showErrorMessage(`LSP Demo: не удалось запустить сервер: ${err.message}`),
  );
}

function deactivate() {
  return client?.stop();
}

module.exports = { activate, deactivate };
