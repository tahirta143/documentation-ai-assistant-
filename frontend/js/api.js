/**
 * api.js — centralized fetch wrapper for all backend endpoints.
 *
 * Automatically attaches JWT Authorization headers and manages SSE streaming.
 */

const API_BASE = '/api';

// ------------------------------------------------------------------ //
// Core fetch helper with JWT Header & 401 Redirect
// ------------------------------------------------------------------ //
async function request(method, path, body = null, isFormData = false) {
  const headers = {};
  const token = localStorage.getItem('docs_assistant_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let bodyPayload = null;

  if (body && !isFormData) {
    headers['Content-Type'] = 'application/json';
    bodyPayload = JSON.stringify(body);
  } else if (isFormData) {
    bodyPayload = body; // FormData — browser sets boundary automatically
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: bodyPayload,
  });

  if (res.status === 401 && !path.startsWith('/auth/')) {
    localStorage.removeItem('docs_assistant_token');
    localStorage.removeItem('docs_assistant_user');
    window.location.href = '/static/login.html';
    throw new Error('Session expired. Please log in again.');
  }

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
// Auth Endpoints
// ------------------------------------------------------------------ //
export const authApi = {
  register: (email, password) =>
    request('POST', '/auth/register', { email, password }),
  login: (email, password) =>
    request('POST', '/auth/login', { email, password }),
  me: () =>
    request('GET', '/auth/me'),
};

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
  ingestUrl: (url) =>
    request('POST', '/documents/url', { url }),
  list: (skip = 0, limit = 50) =>
    request('GET', `/documents?skip=${skip}&limit=${limit}`),
  get: (id) => request('GET', `/documents/${id}`),
  delete: (id) => request('DELETE', `/documents/${id}`),
};

// ------------------------------------------------------------------ //
// Chat & Streaming
// ------------------------------------------------------------------ //
export const chat = {
  send: (question, conversationId = null, documentIds = null) =>
    request('POST', '/chat', {
      question,
      conversation_id: conversationId,
      document_ids: documentIds,
    }),

  stream: async (
    question,
    conversationId = null,
    documentIds = null,
    onToken = () => {},
    onSources = () => {},
    onDone = () => {},
    onError = () => {}
  ) => {
    const token = localStorage.getItem('docs_assistant_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          question,
          conversation_id: conversationId,
          document_ids: documentIds,
        }),
      });

      if (res.status === 401) {
        localStorage.removeItem('docs_assistant_token');
        window.location.href = '/static/login.html';
        return;
      }

      if (!res.ok) {
        let errData;
        try { errData = await res.json(); } catch { errData = null; }
        throw new Error(errData?.detail || `HTTP ${res.status}: ${res.statusText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const jsonStr = trimmed.slice(5).trim();
          try {
            const data = JSON.parse(jsonStr);
            if (data.error) {
              onError(new Error(data.error));
              return;
            }
            if (data.token) {
              onToken(data.token);
            }
            if (data.sources) {
              onSources(data.sources);
            }
            if (data.done) {
              onDone();
            }
          } catch (err) {
            console.warn('Could not parse SSE JSON line:', jsonStr, err);
          }
        }
      }
      onDone();
    } catch (err) {
      onError(err);
    }
  },

  listConversations: (skip = 0, limit = 50) =>
    request('GET', `/conversations?skip=${skip}&limit=${limit}`),
  getConversation: (id) => request('GET', `/conversations/${id}`),
  deleteConversation: (id) => request('DELETE', `/conversations/${id}`),
};
