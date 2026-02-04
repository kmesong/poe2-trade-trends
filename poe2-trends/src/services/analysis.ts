import type { JobResponse, ItemAnalysis } from '../types';

export const startDistributionAnalysis = async (baseType: string): Promise<string> => {
  const response = await fetch('/api/analyze/distribution', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ base_type: baseType }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to start analysis');
  }

  const data = await response.json();
  return data.job_id;
};

export const getAnalysisStatus = async (jobId: string): Promise<JobResponse> => {
  const response = await fetch(`/api/jobs/${jobId}`);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to get job status');
  }

  return await response.json();
};

export const getDistributionResults = async (baseType: string): Promise<ItemAnalysis[]> => {
  const params = new URLSearchParams({ base_type: baseType });
  const response = await fetch(`/api/db/item-analyses?${params.toString()}`);

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to fetch analysis results');
  }

  const result = await response.json();
  return result.data;
};
