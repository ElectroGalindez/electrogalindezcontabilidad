const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const path = require("path");

const STREAMLIT_URL = "http://localhost:8501";
const MAX_WAIT_MS = 30_000;
const POLL_INTERVAL_MS = 500;

let pythonProcess = null;
let mainWindow = null;

function logInfo(message) {
  console.log(`[ElectroGalindez] ${message}`);
}

function logError(message, error) {
  console.error(`[ElectroGalindez] ${message}`);
  if (error) {
    console.error(error);
  }
}

function resolveExecutablePath() {
  const executableName = process.platform === "win32" ? "ElectroGalindez.exe" : "ElectroGalindez";
  const resourcePath = app.isPackaged ? process.resourcesPath : __dirname;
  const distPath = path.join(resourcePath, "dist", executableName);
  if (fs.existsSync(distPath)) {
    return distPath;
  }
  return path.join(__dirname, "dist", executableName);
}

function startPythonExecutable() {
  const executablePath = resolveExecutablePath();
  logInfo(`Iniciando ejecutable: ${executablePath}`);

  pythonProcess = spawn(executablePath, [], {
    stdio: "inherit",
  });

  pythonProcess.on("error", (error) => {
    logError("Error al iniciar el ejecutable Python.", error);
    app.quit();
  });

  pythonProcess.on("exit", (code, signal) => {
    logInfo(`El ejecutable Python finalizó. code=${code} signal=${signal}`);
  });
}

function waitForStreamlit() {
  logInfo(`Esperando servidor en ${STREAMLIT_URL}`);
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(STREAMLIT_URL, (res) => {
        res.resume();
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 500) {
          resolve();
          return;
        }
        retry();
      });

      req.on("error", retry);
      req.setTimeout(2_000, () => {
        req.destroy();
        retry();
      });
    };

    const retry = () => {
      if (Date.now() - start >= MAX_WAIT_MS) {
        reject(new Error(`Timeout esperando a Streamlit (${MAX_WAIT_MS}ms).`));
        return;
      }
      setTimeout(attempt, POLL_INTERVAL_MS);
    };

    attempt();
  });
}

async function createWindow() {
  try {
    startPythonExecutable();
    await waitForStreamlit();

    mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
      },
    });

    await mainWindow.loadURL(STREAMLIT_URL);
    logInfo("Ventana Electron abierta.");

    mainWindow.on("closed", () => {
      mainWindow = null;
      cleanupAndExit();
    });
  } catch (error) {
    logError("No se pudo iniciar la app.", error);
    app.quit();
  }
}

function cleanupAndExit() {
  if (pythonProcess && !pythonProcess.killed) {
    logInfo("Cerrando ejecutable Python...");
    pythonProcess.kill(process.platform === "win32" ? "SIGTERM" : "SIGTERM");
  }
}

app.whenReady().then(createWindow);

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on("before-quit", cleanupAndExit);

app.on("window-all-closed", () => {
  cleanupAndExit();
  if (process.platform !== "darwin") {
    app.quit();
  }
});
