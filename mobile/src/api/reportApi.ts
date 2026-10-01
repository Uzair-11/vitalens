import { apiClient } from './client';
import { MedicalReportSummary, MedicalReportDetail } from '../types';
import { Platform } from 'react-native';

export const reportApi = {
  uploadReport: async (fileUri: string, fileName: string, mimeType: string) => {
    const formData = new FormData();

    if (Platform.OS === 'web') {
      if (fileUri.startsWith('demo://')) {
        // Create sample valid PDF blob for instant demo testing
        const sampleText = `%PDF-1.4\n1 0 obj\n<< /Title (Comprehensive Metabolic Panel & Complete Blood Count) >>\nendobj\n` +
          `Test Name | Observed Value | Unit | Reference Range\n` +
          `Hemoglobin | 11.2 | g/dL | 12.0 - 16.0\n` +
          `White Blood Cell (WBC) | 12.4 | cells/mcL | 4000 - 11000\n` +
          `Fasting Blood Glucose | 118.0 | mg/dL | 70.0 - 99.0\n` +
          `HbA1c | 6.8 | % | 4.0 - 5.6\n` +
          `Total Cholesterol | 225.0 | mg/dL | 125.0 - 200.0\n` +
          `Triglycerides | 185.0 | mg/dL | 0.0 - 150.0\n` +
          `Alanine Aminotransferase (ALT) | 42.0 | U/L | 7.0 - 56.0\n` +
          `Serum Creatinine | 0.9 | mg/dL | 0.6 - 1.2\n` +
          `Thyroid Stimulating Hormone (TSH) | 2.8 | uIU/mL | 0.4 - 4.0\n` +
          `%%EOF\n`;
        const blob = new Blob([sampleText], { type: 'application/pdf' });
        formData.append('file', blob, fileName);
      } else {
        try {
          const res = await fetch(fileUri);
          const blob = await res.blob();
          formData.append('file', blob, fileName);
        } catch (e) {
          formData.append('file', new Blob(['sample data'], { type: mimeType }), fileName);
        }
      }
    } else {
      // In React Native on Android / iOS
      formData.append('file', {
        uri: fileUri,
        name: fileName || 'medical_report.pdf',
        type: mimeType || 'application/pdf',
      } as any);
    }

    console.log('📤 [reportApi.uploadReport] Uploading document payload:', {
      fileName,
      mimeType,
      platform: Platform.OS,
      uriPreview: fileUri.length > 60 ? `${fileUri.substring(0, 60)}...` : fileUri,
    });

    const response = await apiClient.post('/reports/upload', formData, {
      headers: {
        Accept: 'application/json',
      },
      transformRequest: (data) => data,
    });

    console.log('📥 [reportApi.uploadReport] Upload successful! Report ID:', response.data?.report_id);
    return response.data;
  },

  analyzeReport: async (reportId: string): Promise<MedicalReportDetail> => {
    console.log(`🔬 [reportApi.analyzeReport] Initiating analysis for report ID: ${reportId}`);
    const response = await apiClient.post(`/reports/${reportId}/analyze`);
    console.log(`✅ [reportApi.analyzeReport] Analysis completed for report ID: ${reportId}`);
    return response.data;
  },

  getAllReports: async (): Promise<MedicalReportSummary[]> => {
    const response = await apiClient.get('/reports/');
    return response.data;
  },

  getReportDetail: async (reportId: string): Promise<MedicalReportDetail> => {
    const response = await apiClient.get(`/reports/${reportId}`);
    return response.data;
  },

  deleteReport: async (reportId: string) => {
    const response = await apiClient.delete(`/reports/${reportId}`);
    return response.data;
  },
};
