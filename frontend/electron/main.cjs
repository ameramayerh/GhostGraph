const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const path = require("path");

let mainWindow;
let backendProcess;

function backendIsReady() {
  return new Promise((resolve) => {
    const request = http.get("http://127.0.0.1:8000/api/health", (response) => {
      response.resume();
      resolve(response.statusCode === 200);
    });
    request.setTimeout(1000, () => {
      request.destroy();
      resolve(false);
    });
    request.on("error", () => resolve(false));
  });
}

function getBackendPaths() {
  const projectRoot = path.resolve(__dirname, "..", "..");
  const sourceBackend = path.join(projectRoot, "backend");
  const packagedBackend = path.join(process.resourcesPath, "backend");
  const backendDirectory = app.isPackaged ? packagedBackend : sourceBackend;
  const bundledPython = path.join(sourceBackend, ".venv", "Scripts", "python.exe");

  return {
    backendDirectory,
    python: process.env.GHOSTGRAPH_PYTHON || (fs.existsSync(bundledPython) ? bundledPython : "python"),
  };
}

async function startBackend() {
  if (await backendIsReady()) return;

  const { backendDirectory, python } = getBackendPaths();
  backendProcess = spawn(
    python,
    ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    { cwd: backendDirectory, windowsHide: true }
  );

  backendProcess.on("error", (error) => {
    dialog.showErrorBox("GhostGraph backend could not start", error.message);
  });

  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (await backendIsReady()) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error("The GhostGraph backend did not become ready on port 8000.");
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    title: "GhostGraph",
    icon: path.join(__dirname, "..", "dist", "logo.png"),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.cjs"),
    },
  });

  mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
}

app.whenReady().then(async () => {
  try {
    await startBackend();
    createWindow();
  } catch (error) {
    dialog.showErrorBox("GhostGraph could not start", error.message);
    app.quit();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess && !backendProcess.killed) backendProcess.kill();
});
