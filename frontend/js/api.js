/**
 * api.js — centralized fetch wrapper for all backend endpoints.
 *
 * All functions return parsed JSON on success.
 * On HTTP error they throw an Error with a human-readable message.
 */

const API_BASE = '/api';

// ------------------------------------------------------------------ //
// Core fetch helper
// ------------------------------------------------------------------ //
async function request(method, path, body = null, isFormData = false) {
  const headers = {};
  let bodyPayload = null;

  if (body && !isFormData) {
    headers['Content-Type'] = 'application/json';
    bodyPayload = JSON.stringify(body);
  } else if (isFormData) {
    bodyPayload = body; // FormData — browser sets Content-Type automatically
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: bodyPayload,
  });

  if (res.status === 204) return null; // No Content

  let data;
  try { data = await res.json(); } catch { data = null; }

  if (!res.ok) {
    const msg = data?.detail || `HTTP ${res.status}: ${res.statusText}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }

  return data;
}

// ------------------------------------------------------------------ //
// Health
// ------------------------------------------------------------------ //
export const health = {
  get: () => request('GET', '/health'),
};

// ------------------------------------------------------------------ //
// Documents
// ------------------------------------------------------------------ //
export const documents = {
  upload: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request('POST', '/documents/upload', fd, true);
  },
  list: (skip = 0, limit = 50) =>
    request('GET', `/documents?skip=${skip}&limit=${limit}`),
  get: (id) => request('GET', `/documents/${id}`),
  delete: (id) => request('DELETE', `/documents/${id}`),
};

// ------------------------------------------------------------------ //
// Chat
// ------------------------------------------------------------------ //
export const chat = {
  send: (question, conversationId = null, documentIds = null) =>
    request('POST', '/chat', {
      question,
      conversation_id: conversationId,
      document_ids: documentIds,
    }),
  listConversations: (skip = 0, limit = 50) =>
    request('GET', `/conversations?skip=${skip}&limit=${limit}`),
  getConversation: (id) => request('GET', `/conversations/${id}`),
  deleteConversation: (id) => request('DELETE', `/conversations/${id}`),
};
