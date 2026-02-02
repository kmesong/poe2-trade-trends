export const STORAGE_KEY_SESSION_ID = 'poe_session_id';

export const saveSessionId = (sessionId: string): void => {
  if (!sessionId) {
    localStorage.removeItem(STORAGE_KEY_SESSION_ID);
    return;
  }
  localStorage.setItem(STORAGE_KEY_SESSION_ID, sessionId);
};

export const getSessionId = (): string | null => {
  return localStorage.getItem(STORAGE_KEY_SESSION_ID);
};
