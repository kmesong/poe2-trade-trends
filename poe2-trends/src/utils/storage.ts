import type { BatchResult } from '../types';

export const STORAGE_KEY_SESSION_ID = 'poe_session_id';
export const STORAGE_KEY_BATCH_INPUT = 'poe_batch_input';
export const STORAGE_KEY_BATCH_RESULTS = 'poe_batch_results';

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

export const saveBatchInput = (input: string): void => {
  localStorage.setItem(STORAGE_KEY_BATCH_INPUT, input);
};

export const getBatchInput = (): string => {
  return localStorage.getItem(STORAGE_KEY_BATCH_INPUT) || '';
};

export const saveBatchResults = (results: BatchResult[]): void => {
  localStorage.setItem(STORAGE_KEY_BATCH_RESULTS, JSON.stringify(results));
};

export const getBatchResults = (): BatchResult[] => {
  const stored = localStorage.getItem(STORAGE_KEY_BATCH_RESULTS);
  if (!stored) return [];
  try {
    return JSON.parse(stored) as BatchResult[];
  } catch {
    return [];
  }
};
