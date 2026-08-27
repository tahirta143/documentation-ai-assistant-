/**
 * Authentication and session manager.
 */

const TOKEN_KEY = 'docs_assistant_token';
const USER_KEY = 'docs_assistant_user';

export const auth = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(USER_KEY);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
  },

  clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  isAuthenticated() {
    return Boolean(this.getToken());
  },

  logout() {
    this.clearSession();
    window.location.href = '/static/login.html';
  },

  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = '/static/login.html';
      return false;
    }
    return true;
  }
};
