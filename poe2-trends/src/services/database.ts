import type { AnalysisResultDB, ExcludedModifier } from '../types';

const API_BASE = '/api/db';

export async function getExclusions(): Promise<ExcludedModifier[]> {
  const response = await fetch(`${API_BASE}/exclusions`);
  if (!response.ok) {
    throw new Error('Failed to fetch exclusions');
  }
  const data = await response.json();
  return data.data;
}

export async function addExclusion(exclusion: Partial<ExcludedModifier>): Promise<ExcludedModifier> {
  const response = await fetch(`${API_BASE}/exclusions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(exclusion),
  });
  if (!response.ok) {
    throw new Error('Failed to add exclusion');
  }
  const data = await response.json();
  return data.data;
}

export async function removeExclusion(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/exclusions/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to remove exclusion');
  }
}

export async function updateExclusion(id: number, exclusion: Partial<ExcludedModifier>): Promise<ExcludedModifier> {
  const response = await fetch(`${API_BASE}/exclusions/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(exclusion),
  });
  if (!response.ok) {
    throw new Error('Failed to update exclusion');
  }
  const data = await response.json();
  return data.data;
}

export async function getAnalyses(baseType?: string, limit: number = 100): Promise<AnalysisResultDB[]> {
  const params = new URLSearchParams();
  if (baseType) params.append('base_type', baseType);
  params.append('limit', limit.toString());

  const response = await fetch(`${API_BASE}/analyses?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch analyses');
  }
  const data = await response.json();
  return data.data;
}

export async function getAnalysis(id: number): Promise<AnalysisResultDB> {
  const response = await fetch(`${API_BASE}/analyses/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch analysis');
  }
  const data = await response.json();
  return data.data;
}
