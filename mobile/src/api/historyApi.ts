import { apiClient } from './client';
import { BiomarkerTrendSeries, ReportComparisonData } from '../types';

export const historyApi = {
  getTrends: async (canonicalNames: string[]): Promise<BiomarkerTrendSeries[]> => {
    const params = new URLSearchParams();
    canonicalNames.forEach((name) => params.append('canonical_names', name));
    const response = await apiClient.get('/history/trends', { params });
    return response.data;
  },

  compareReports: async (report1Id: string, report2Id: string): Promise<ReportComparisonData> => {
    const response = await apiClient.get('/history/compare', {
      params: { report_1_id: report1Id, report_2_id: report2Id },
    });
    return response.data;
  },
};
