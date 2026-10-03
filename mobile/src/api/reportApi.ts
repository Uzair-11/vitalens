import { apiClient } from './client';
import { MedicalReportSummary, MedicalReportDetail } from '../types';
import { Platform } from 'react-native';
import { API_CONFIG } from '../constants/config';
import { useAuthStore } from '../store/authStore';

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

    const formData = new FormData();

    if (Platform.OS === 'web') {
      const blob = await getFileBlob(fileUri, resolvedMime);
      console.log('📦 [reportApi.uploadReport] Web Blob created. Size:', blob.size, 'Type:', blob.type);
      formData.append('file', blob, resolvedFileName);
    } else {
      // In React Native on Android & iOS:
      // Passing { uri, name, type } streams the binary directly from native disk via OkHttp/NSURLSession.
      // This completely avoids calling Response.blob(), avoiding bridge base64 copies and memory overhead.
      console.log('📦 [reportApi.uploadReport] Using native direct file streaming (zero-copy)');
      formData.append('file', {
        uri: fileUri,
        name: resolvedFileName,
        type: resolvedMime,
      } as any);
    }

    const headers: Record<string, string> = {
      Accept: 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    console.log(`📡 [API REQ] POST ${url} (multipart upload)`);

    // First try standard fetch with the Blob
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      const resData = await response.json().catch(() => null);

      if (!response.ok) {
        console.error(`❌ [API ERR] POST ${url} | Status: ${response.status}`, resData);
        const errorDetail = resData?.detail || `Upload failed with status ${response.status}`;
        const err: any = new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
        err.response = { status: response.status, data: resData };
        throw err;
      }

      console.log(`✅ [API RES] ${response.status} POST /reports/upload`);
      console.log('📥 [reportApi.uploadReport] Upload successful! Report ID:', resData?.report_id);
      return resData;
    } catch (fetchErr: any) {
      if (fetchErr.response) {
        throw fetchErr;
      }

      console.log('ℹ️ [reportApi.uploadReport] fetch failed, falling back to XHR POST:', fetchErr.message);

      // Resilient fallback: Upload via XMLHttpRequest
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        xhr.setRequestHeader('Accept', 'application/json');
        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        }

        xhr.onload = () => {
          let data: any = null;
          try {
            data = JSON.parse(xhr.responseText);
          } catch {
            data = xhr.responseText;
          }

          if (xhr.status >= 200 && xhr.status < 300) {
            console.log(`✅ [API RES] ${xhr.status} POST /reports/upload (via XHR)`);
            resolve(data);
          } else {
            console.error(`❌ [API ERR] POST ${url} | Status: ${xhr.status} (via XHR)`, data);
            const errorDetail = data?.detail || `Upload failed with status ${xhr.status}`;
            const err: any = new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
            err.response = { status: xhr.status, data };
            reject(err);
          }
        };

        xhr.onerror = (e) => {
          console.error('❌ [API ERR] XHR POST failed:', e);
          reject(new Error('Network Error: Failed to upload file to backend server.'));
        };

        xhr.send(formData);
      });
    }
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
