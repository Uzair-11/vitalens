import { apiClient } from './client';
import { SpecialtyRecommendationResult } from '../types';

export const aiApi = {
  logSymptoms: async (symptomData: {
    report_id?: string;
    primary_concern: string;
    symptoms_list: string[];
    duration_days: number;
    severity_score: number;
    body_region: string;
    additional_notes?: string;
  }) => {
    const response = await apiClient.post('/ai/symptoms', symptomData);
    return response.data;
  },

  recommendSpecialty: async (data: {
    report_id?: string;
    symptom_log_id: string;
  }): Promise<SpecialtyRecommendationResult> => {
    const response = await apiClient.post('/ai/recommend-specialty', data);
    return response.data;
  },

  askReportQuestion: async (reportId: string, question: string) => {
    const response = await apiClient.post('/ai/qa', {
      report_id: reportId,
      question: question,
    });
    return response.data;
  },
};
