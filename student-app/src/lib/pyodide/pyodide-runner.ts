/**
 * Pyodide Runner — executes Python code in the browser via WebAssembly.
 * Loads Pyodide from CDN (not npm) to avoid Node.js module issues with webpack.
 */

declare global {
  interface Window {
    loadPyodide?: (config: { indexURL: string }) => Promise<PyodideInterface>;
  }
}

interface PyodideInterface {
  runPython: (code: string) => unknown;
  runPythonAsync: (code: string) => Promise<unknown>;
}

const PYODIDE_VERSION = '0.27.5';
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

let pyodideInstance: PyodideInterface | null = null;
let loadingPromise: Promise<void> | null = null;

export interface PythonResult {
  stdout: string;
  stderr: string;
  error: string | null;
  executionTimeMs: number;
}

const EXECUTION_TIMEOUT_MS = 10_000;

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(script);
  });
}

/**
 * Lazily load Pyodide singleton. First call downloads ~11MB WASM (cached by browser).
 */
export async function ensurePyodideLoaded(
  onProgress?: (msg: string) => void
): Promise<void> {
  if (pyodideInstance) return;

  if (loadingPromise) {
    await loadingPromise;
    return;
  }

  loadingPromise = (async () => {
    onProgress?.('loading');
    // Load Pyodide script from CDN
    await loadScript(`${PYODIDE_CDN}pyodide.js`);

    if (!window.loadPyodide) {
      throw new Error('Pyodide failed to load from CDN');
    }

    pyodideInstance = await window.loadPyodide({
      indexURL: PYODIDE_CDN,
    });
    onProgress?.('ready');
  })();

  try {
    await loadingPromise;
  } catch (err) {
    loadingPromise = null;
    throw err;
  }
}

/**
 * Run Python code with stdin support and timeout.
 */
export async function runPython(
  code: string,
  stdinLines: string = ''
): Promise<PythonResult> {
  await ensurePyodideLoaded();
  const py = pyodideInstance!;

  const start = performance.now();

  // Prepare stdin buffer for input() calls
  const stdinArray = stdinLines
    .split('\n')
    .map((line) => line)
    .reverse(); // reverse so we can pop()

  // Setup stdout/stderr capture and stdin override
  py.runPython(`
import sys
from io import StringIO

class _StdinBuffer:
    def __init__(self, lines):
        self._lines = lines
    def readline(self):
        if self._lines:
            return self._lines.pop() + "\\n"
        return ""

_stdout_buf = StringIO()
_stderr_buf = StringIO()
sys.stdout = _stdout_buf
sys.stderr = _stderr_buf
sys.stdin = _StdinBuffer(${JSON.stringify(stdinArray)})
`);

  let error: string | null = null;

  try {
    // Run with timeout
    await Promise.race([
      (async () => {
        try {
          await py.runPythonAsync(code);
        } catch (err: unknown) {
          const pyErr = err as Error;
          error = pyErr.message || String(err);
        }
      })(),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('__TIMEOUT__')), EXECUTION_TIMEOUT_MS)
      ),
    ]);
  } catch (err: unknown) {
    const e = err as Error;
    if (e.message === '__TIMEOUT__') {
      error = 'TimeoutError: Превышено время выполнения (10 сек). Возможно, бесконечный цикл.';
      // Reset Pyodide after timeout (infinite loop may have corrupted state)
      pyodideInstance = null;
      loadingPromise = null;
    } else {
      error = e.message || String(err);
    }
  }

  let stdout = '';
  let stderr = '';

  try {
    stdout = (py.runPython('_stdout_buf.getvalue()') as string) || '';
    stderr = (py.runPython('_stderr_buf.getvalue()') as string) || '';
    // Restore sys streams
    py.runPython(`
import sys
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
sys.stdin = sys.__stdin__
`);
  } catch {
    // If pyodide was reset due to timeout, we can't read buffers
  }

  const executionTimeMs = Math.round(performance.now() - start);

  return { stdout, stderr, error, executionTimeMs };
}

/**
 * Check if Pyodide is currently loaded and ready.
 */
export function isPyodideReady(): boolean {
  return pyodideInstance !== null;
}
