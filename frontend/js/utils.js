/**
 * utils.js — shared frontend helpers.
 */

// ------------------------------------------------------------------ //
// HTML escaping — ALWAYS escape user content before inserting to DOM
// ------------------------------------------------------------------ //
export function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ------------------------------------------------------------------ //
// Date formatting
// ------------------------------------------------------------------ //
export function formatDate(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

export function formatDateTime(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function timeAgo(isoString) {
  if (!isoString) return '';
  const seconds = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (seconds < 60)   return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return formatDate(isoString);
}

// ------------------------------------------------------------------ //
// File helpers
// ------------------------------------------------------------------ //
export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function fileTypeIcon(fileType) {
  const icons = { pdf: '📄', md: '📝', txt: '📃', url: '🌐' };
  return icons[fileType] || '📁';
}

export function statusBadge(status) {
  const map = {
    ready:      ['badge-success', '✓ Ready'],
    processing: ['badge-warning', '⏳ Processing'],
    failed:     ['badge-danger',  '✗ Failed'],
  };
  const [cls, label] = map[status] || ['badge-neutral', status];
  return `<span class="badge ${cls}">${label}</span>`;
}

// ------------------------------------------------------------------ //
// Toast notifications
// ------------------------------------------------------------------ //
let _toastContainer = null;

function getToastContainer() {
  if (!_toastContainer) {
    _toastContainer = document.createElement('div');
    _toastContainer.className = 'toast-container';
    document.body.appendChild(_toastContainer);
  }
  return _toastContainer;
}

export function toast(message, type = 'info', duration = 3500) {
  const icons = { success: '✓', error: '✗', info: 'ℹ' };
  const container = getToastContainer();
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.3s';
    setTimeout(() => el.remove(), 300);
  }, duration);
}

// ------------------------------------------------------------------ //
// Simple markdown → safe HTML (no external lib needed for basic cases)
// ------------------------------------------------------------------ //
export function renderMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Code blocks (``` ... ```)
  html = html.replace(/```[\w]*\n?([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  // Inline code
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm,  '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm,   '<h1>$1</h1>');
  // Unordered lists
  html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // Paragraphs (double newline)
  html = html.split(/\n\n+/).map(p =>
    p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<pre') || p.startsWith('<li')
      ? p
      : `<p>${p.replace(/\n/g, '<br>')}</p>`
  ).join('');

  return html;
}
