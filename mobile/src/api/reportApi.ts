import { apiClient } from './client';
import { MedicalReportSummary, MedicalReportDetail } from '../types';
import { Platform } from 'react-native';
import { API_CONFIG } from '../constants/config';
import { useAuthStore } from '../store/authStore';
import * as FileSystem from 'expo-file-system/legacy';

export const getFileBlob = async (fileUri: string, mimeType: string): Promise<Blob> => {
  if (Platform.OS === 'web' && fileUri.startsWith('demo://')) {
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
    return new Blob([sampleText], { type: 'application/pdf' });
  }

  // 1. Try standard fetch to convert URI to Blob
  try {
    const res = await fetch(fileUri);
    const blob = await res.blob();
    if (blob && (blob.size > 0 || (blob as any)._data?.size > 0)) {
      return blob;
    }
  } catch (fetchErr) {
    console.log('ℹ️ [reportApi] fetch(uri) could not read local file blob, falling back to XHR:', fetchErr);
  }

  // 2. Fallback to XMLHttpRequest with responseType = 'blob' (handles React Native / Android cache files)
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.onload = () => {
      if (xhr.response) {
        resolve(xhr.response as Blob);
      } else {
        reject(new Error('XHR returned empty file blob'));
      }
    };
    xhr.onerror = (e) => {
      reject(new Error(`Failed to read file from URI: ${fileUri}`));
    };
    xhr.responseType = 'blob';
    xhr.open('GET', fileUri, true);
    xhr.send(null);
  });
};

export const reportApi = {
  uploadReport: async (fileUri: string, fileName: string, mimeType: string) => {
    const token = useAuthStore.getState().token;
    const url = `${API_CONFIG.BASE_URL}/reports/upload`;
    const resolvedFileName = fileName || 'medical_report.pdf';
    const resolvedMime = mimeType || 'application/pdf';

    console.log('📤 [reportApi.uploadReport] Preparing upload payload:', {
      fileName: resolvedFileName,
      mimeType: resolvedMime,
      platform: Platform.OS,
      uriPreview: fileUri.length > 60 ? `${fileUri.substring(0, 60)}...` : fileUri,
    });

    // 1. On Native Mobile (Android & iOS): Use FileSystem.uploadAsync
    // This streams the file directly from Android SAF content:// or file:// URI via native OkHttp/NSURLSession.
    // Completely avoids JS-side closed stream / base64 memory issues.
    if (Platform.OS !== 'web' && (fileUri.startsWith('file://') || fileUri.startsWith('content://'))) {
      try {
        console.log(`📡 [API REQ] FileSystem.uploadAsync ${url}`);
        const uploadResult = await FileSystem.uploadAsync(url, fileUri, {
          httpMethod: 'POST',
          uploadType: FileSystem.FileSystemUploadType.MULTIPART,
          fieldName: 'file',
          mimeType: resolvedMime,
          headers: {
            Accept: 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });

        let resData: any = null;
        try {
          resData = JSON.parse(uploadResult.body);
        } catch {
          resData = uploadResult.body;
        }

        if (uploadResult.status >= 200 && uploadResult.status < 300) {
          console.log(`✅ [API RES] ${uploadResult.status} POST /reports/upload (FileSystem.uploadAsync)`);
          console.log('📥 [reportApi.uploadReport] Upload successful! Report ID:', resData?.report_id);
          return resData;
        } else {
          console.error(`❌ [API ERR] FileSystem.uploadAsync status ${uploadResult.status}:`, resData);
          const errorDetail = resData?.detail || `Upload failed with status ${uploadResult.status}`;
          const err: any = new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
          err.response = { status: uploadResult.status, data: resData };
          throw err;
        }
      } catch (nativeErr: any) {
        if (nativeErr.response) {
          throw nativeErr;
        }
        console.warn('⚠️ [reportApi.uploadReport] FileSystem.uploadAsync encountered network error, trying fallback:', nativeErr.message);
      }
    }

    // 2. Web or fallback: Standard FormData upload via apiClient
    const formData = new FormData();
    if (Platform.OS === 'web') {
      const blob = await getFileBlob(fileUri, resolvedMime);
      formData.append('file', blob, resolvedFileName);
    } else {
      formData.append('file', {
        uri: fileUri,
        name: resolvedFileName,
        type: resolvedMime,
      } as any);
    }

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
    const response = await apiClient.post(`/reports/${reportId}/analyze`, null, {
      timeout: 90000,
    });
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
