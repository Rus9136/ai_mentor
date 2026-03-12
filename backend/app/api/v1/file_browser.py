"""
Standalone file browser HTML page — served at /files.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Mentor — Файлы</title>
<style>
  :root {
    --bg: #0f172a;
    --surface: #1e293b;
    --surface-hover: #334155;
    --border: #334155;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --green: #22c55e;
    --orange: #f59e0b;
    --red: #ef4444;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }
  .header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .header h1 {
    font-size: 20px;
    font-weight: 600;
  }
  .header .logo {
    width: 32px; height: 32px;
    background: var(--accent);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px;
  }
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
  }
  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 20px;
    font-size: 14px;
    color: var(--text-muted);
    flex-wrap: wrap;
  }
  .breadcrumb a {
    color: var(--accent);
    text-decoration: none;
    cursor: pointer;
  }
  .breadcrumb a:hover { text-decoration: underline; }
  .breadcrumb .sep { color: var(--text-muted); }

  .file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
  }
  .file-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .file-card:hover {
    background: var(--surface-hover);
    border-color: var(--accent);
    transform: translateY(-1px);
  }
  .file-icon {
    width: 44px; height: 44px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
  }
  .icon-folder { background: #1e3a5f; color: #60a5fa; }
  .icon-pdf { background: #3b1c1c; color: #f87171; }
  .icon-image { background: #1c3b2a; color: #4ade80; }
  .icon-doc { background: #1c2d3b; color: #60a5fa; }
  .icon-video { background: #3b1c3b; color: #c084fc; }
  .icon-audio { background: #3b2d1c; color: #fbbf24; }
  .icon-archive { background: #2d2d1c; color: #a3a310; }
  .icon-code { background: #1c3b3b; color: #2dd4bf; }
  .icon-default { background: #2d2d3b; color: #94a3b8; }

  .file-info {
    flex: 1;
    min-width: 0;
  }
  .file-name {
    font-weight: 500;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .file-meta {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 3px;
  }
  .file-actions {
    display: flex;
    gap: 6px;
    flex-shrink: 0;
  }
  .btn {
    padding: 6px 10px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.15s;
  }
  .btn-preview {
    background: var(--accent);
    color: white;
  }
  .btn-preview:hover { background: var(--accent-hover); }
  .btn-download {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
  }
  .btn-download:hover {
    border-color: var(--accent);
    color: var(--text);
  }

  .empty {
    text-align: center;
    padding: 80px 20px;
    color: var(--text-muted);
  }
  .empty .icon { font-size: 48px; margin-bottom: 16px; }
  .empty p { font-size: 16px; }

  .loading {
    text-align: center;
    padding: 60px;
    color: var(--text-muted);
  }
  .spinner {
    width: 32px; height: 32px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Preview modal */
  .modal-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.8);
    z-index: 1000;
    justify-content: center;
    align-items: center;
  }
  .modal-overlay.active { display: flex; }
  .modal {
    background: var(--surface);
    border-radius: 16px;
    width: 90vw;
    height: 90vh;
    max-width: 1100px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
  }
  .modal-header h3 {
    font-size: 15px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
    margin-right: 12px;
  }
  .modal-header .actions { display: flex; gap: 8px; }
  .modal-body {
    flex: 1;
    overflow: auto;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    background: #0a0f1e;
  }
  .modal-body iframe {
    width: 100%;
    height: 100%;
    border: none;
    border-radius: 8px;
    background: white;
  }
  .modal-body img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 8px;
  }
  .modal-body video, .modal-body audio {
    max-width: 100%;
    border-radius: 8px;
  }
  .modal-body .text-preview {
    width: 100%;
    height: 100%;
    background: var(--surface);
    color: var(--text);
    border-radius: 8px;
    padding: 20px;
    overflow: auto;
    font-family: 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .no-preview {
    text-align: center;
    color: var(--text-muted);
  }
  .no-preview .icon { font-size: 64px; margin-bottom: 16px; }
  .btn-close {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text);
    width: 32px; height: 32px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .btn-close:hover { background: var(--surface-hover); }

  @media (max-width: 640px) {
    .container { padding: 16px; }
    .file-grid { grid-template-columns: 1fr; }
    .modal { width: 100vw; height: 100vh; border-radius: 0; }
    .file-actions { flex-direction: column; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="logo">AI</div>
  <h1>Shared Files</h1>
</div>

<div class="container">
  <div class="breadcrumb" id="breadcrumb"></div>
  <div id="content">
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading...</p>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-header">
      <h3 id="modal-title"></h3>
      <div class="actions">
        <a id="modal-download" class="btn btn-download" download>Download</a>
        <button class="btn-close" onclick="closeModal()">&times;</button>
      </div>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>

<script>
const API = window.location.origin + '/api/v1/shared-files';
let currentPath = '';

function getIcon(item) {
  if (item.type === 'directory') return { cls: 'icon-folder', icon: '&#128193;' };
  const ext = item.name.split('.').pop().toLowerCase();
  const mime = item.mime_type || '';
  if (ext === 'pdf') return { cls: 'icon-pdf', icon: '&#128196;' };
  if (['jpg','jpeg','png','gif','svg','webp','bmp'].includes(ext)) return { cls: 'icon-image', icon: '&#128247;' };
  if (['mp4','webm','mov','avi','mkv'].includes(ext)) return { cls: 'icon-video', icon: '&#127909;' };
  if (['mp3','wav','ogg','flac','aac'].includes(ext)) return { cls: 'icon-audio', icon: '&#127925;' };
  if (['doc','docx','xls','xlsx','ppt','pptx'].includes(ext)) return { cls: 'icon-doc', icon: '&#128209;' };
  if (['zip','rar','7z','tar','gz'].includes(ext)) return { cls: 'icon-archive', icon: '&#128230;' };
  if (['js','ts','py','html','css','json','md','mmd','txt','csv'].includes(ext)) return { cls: 'icon-code', icon: '&#128221;' };
  return { cls: 'icon-default', icon: '&#128196;' };
}

function formatSize(bytes) {
  if (!bytes) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
  return bytes.toFixed(i ? 1 : 0) + ' ' + units[i];
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function renderBreadcrumb(path) {
  const bc = document.getElementById('breadcrumb');
  const parts = path ? path.split('/') : [];
  let html = '<a onclick="navigate(\\'\\')">&#127968; Home</a>';
  let accumulated = '';
  for (const part of parts) {
    accumulated += (accumulated ? '/' : '') + part;
    const p = accumulated;
    html += '<span class="sep">/</span>';
    html += `<a onclick="navigate('${p}')">${part}</a>`;
  }
  bc.innerHTML = html;
}

function canPreview(item) {
  const ext = item.name.split('.').pop().toLowerCase();
  return ['pdf','jpg','jpeg','png','gif','svg','webp','bmp',
          'mp4','webm','mp3','wav','ogg',
          'txt','md','mmd','json','csv','js','ts','py','html','css','xml','log'].includes(ext);
}

function isText(name) {
  const ext = name.split('.').pop().toLowerCase();
  return ['txt','md','mmd','json','csv','js','ts','py','html','css','xml','log','yaml','yml','toml','ini','cfg','sh','bat','sql'].includes(ext);
}

async function navigate(path) {
  currentPath = path;
  renderBreadcrumb(path);
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';

  try {
    const res = await fetch(API + '/list?dir=' + encodeURIComponent(path));
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();

    if (data.items.length === 0) {
      content.innerHTML = '<div class="empty"><div class="icon">&#128194;</div><p>No files yet. Place files in the shared-files/ folder.</p></div>';
      return;
    }

    let html = '<div class="file-grid">';
    for (const item of data.items) {
      const icon = getIcon(item);
      const filePath = currentPath ? currentPath + '/' + item.name : item.name;

      if (item.type === 'directory') {
        html += `
          <div class="file-card" onclick="navigate('${filePath}')">
            <div class="file-icon ${icon.cls}">${icon.icon}</div>
            <div class="file-info">
              <div class="file-name">${item.name}</div>
              <div class="file-meta">${formatDate(item.modified)}</div>
            </div>
          </div>`;
      } else {
        const previewable = canPreview(item);
        html += `
          <div class="file-card" ${previewable ? `onclick="openPreview('${filePath}', '${item.name}', '${item.mime_type}')"` : ''}>
            <div class="file-icon ${icon.cls}">${icon.icon}</div>
            <div class="file-info">
              <div class="file-name">${item.name}</div>
              <div class="file-meta">${formatSize(item.size)} &middot; ${formatDate(item.modified)}</div>
            </div>
            <div class="file-actions" onclick="event.stopPropagation()">
              ${previewable ? `<button class="btn btn-preview" onclick="openPreview('${filePath}', '${item.name}', '${item.mime_type}')">Preview</button>` : ''}
              <a class="btn btn-download" href="${API}/download/${encodeURIComponent(filePath)}" download>Download</a>
            </div>
          </div>`;
      }
    }
    html += '</div>';
    content.innerHTML = html;
  } catch (e) {
    content.innerHTML = '<div class="empty"><div class="icon">&#9888;&#65039;</div><p>Error loading files</p></div>';
  }
}

async function openPreview(filePath, name, mime) {
  const modal = document.getElementById('modal');
  const body = document.getElementById('modal-body');
  const title = document.getElementById('modal-title');
  const dlBtn = document.getElementById('modal-download');

  title.textContent = name;
  dlBtn.href = API + '/download/' + encodeURIComponent(filePath);
  const previewUrl = API + '/preview/' + encodeURIComponent(filePath);

  const ext = name.split('.').pop().toLowerCase();

  if (ext === 'pdf') {
    body.innerHTML = `<iframe src="${previewUrl}"></iframe>`;
  } else if (['jpg','jpeg','png','gif','svg','webp','bmp'].includes(ext)) {
    body.innerHTML = `<img src="${previewUrl}" alt="${name}">`;
  } else if (['mp4','webm'].includes(ext)) {
    body.innerHTML = `<video controls src="${previewUrl}"></video>`;
  } else if (['mp3','wav','ogg'].includes(ext)) {
    body.innerHTML = `<div style="width:100%;max-width:500px"><audio controls src="${previewUrl}" style="width:100%"></audio></div>`;
  } else if (isText(name)) {
    body.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    try {
      const res = await fetch(previewUrl);
      const text = await res.text();
      body.innerHTML = `<div class="text-preview">${escapeHtml(text)}</div>`;
    } catch {
      body.innerHTML = '<div class="no-preview"><p>Error loading file</p></div>';
    }
  } else {
    body.innerHTML = `<div class="no-preview"><div class="icon">&#128196;</div><p>Preview not available for this file type</p><a class="btn btn-preview" href="${API}/download/${encodeURIComponent(filePath)}" download style="margin-top:16px;display:inline-block">Download instead</a></div>`;
  }

  modal.classList.add('active');
}

function closeModal() {
  const modal = document.getElementById('modal');
  const body = document.getElementById('modal-body');
  modal.classList.remove('active');
  body.innerHTML = '';
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

navigate('');
</script>
</body>
</html>"""


@router.get("", response_class=HTMLResponse)
async def file_browser_page():
    """Serve the standalone file browser page."""
    return HTML_PAGE
