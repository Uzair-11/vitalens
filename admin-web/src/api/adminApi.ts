import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/v1';

export const adminClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach token
adminClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('vitalens_admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 token refresh and 403 authorization
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

adminClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return adminClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('vitalens_admin_refresh_token');
      if (!refreshToken) {
        localStorage.removeItem('vitalens_admin_token');
        localStorage.removeItem('vitalens_admin_refresh_token');
        localStorage.removeItem('vitalens_admin_role');
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        const refreshRes = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        const newToken = refreshRes.data.access_token;
        localStorage.setItem('vitalens_admin_token', newToken);
        adminClient.defaults.headers.common.Authorization = `Bearer ${newToken}`;
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return adminClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.removeItem('vitalens_admin_token');
        localStorage.removeItem('vitalens_admin_refresh_token');
        localStorage.removeItem('vitalens_admin_role');
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const adminApi = {
  // Auth
  login: async (email: string, password: string) => {
    const res = await axios.post(`${BASE_URL}/auth/login-json`, { email, password });
    const { access_token, refresh_token, role, user_id } = res.data;
    if (role !== 'ADMIN' && role !== 'SUPER_ADMIN' && role !== 'SUPPORT_STAFF' && role !== 'DOCTOR') {
      throw new Error('Access denied: Operations, Doctor, or Administrator account required.');
    }
    localStorage.setItem('vitalens_admin_token', access_token);
    localStorage.setItem('vitalens_admin_refresh_token', refresh_token);
    localStorage.setItem('vitalens_admin_role', role);
    localStorage.setItem('vitalens_admin_user_id', user_id);
    return res.data;
  },

  logout: () => {
    localStorage.removeItem('vitalens_admin_token');
    localStorage.removeItem('vitalens_admin_refresh_token');
    localStorage.removeItem('vitalens_admin_role');
    localStorage.removeItem('vitalens_admin_user_id');
  },

  // Analytics
  getAnalytics: async () => {
    const res = await adminClient.get('/admin/analytics/dashboard');
    return res.data;
  },

  // Doctors
  getSpecialties: async () => {
    const res = await adminClient.get('/doctors/specialties');
    return res.data;
  },

  getDoctors: async (params?: { name?: string; specialty_id?: string; verification_status?: string; is_active?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.name) query.append('name', params.name);
    if (params?.specialty_id) query.append('specialty_id', params.specialty_id);
    if (params?.verification_status) query.append('verification_status', params.verification_status);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    const url = `/admin/doctors/${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  createDoctor: async (data: {
    email: string;
    temporary_password?: string;
    full_name: string;
    specialty_id: string;
    qualification: string;
    experience_years: number;
    clinic_name: string;
    address: string;
    city: string;
    consultation_fee: number;
    bio?: string;
    languages?: string[];
  }) => {
    const res = await adminClient.post('/admin/doctors/', data);
    return res.data;
  },

  verifyDoctor: async (doctorId: string, verificationStatus: 'VERIFIED' | 'REJECTED' | 'PENDING') => {
    const res = await adminClient.patch(`/admin/doctors/${doctorId}/verify?verification_status=${verificationStatus}`);
    return res.data;
  },

  toggleDoctorStatus: async (doctorId: string, isActive: boolean) => {
    const res = await adminClient.patch(`/admin/doctors/${doctorId}/status?is_active=${isActive}`);
    return res.data;
  },

  // Patients / Users
  getUsers: async (params?: { search?: string; role?: string; skip?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.role) query.append('role', params.role);
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    const url = `/admin/users/${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  getUserDetail: async (userId: string) => {
    const res = await adminClient.get(`/admin/users/${userId}`);
    return res.data;
  },

  toggleUserStatus: async (userId: string, isActive: boolean) => {
    const res = await adminClient.patch(`/admin/users/${userId}/status?is_active=${isActive}`);
    return res.data;
  },

  // Appointments
  getAppointments: async (params?: { status?: string; doctor_id?: string; patient_id?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.doctor_id) query.append('doctor_id', params.doctor_id);
    if (params?.patient_id) query.append('patient_id', params.patient_id);
    const url = `/admin/appointments/${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  cancelAppointment: async (appointmentId: string, reason: string) => {
    const res = await adminClient.patch(`/admin/appointments/${appointmentId}/cancel?reason=${encodeURIComponent(reason)}`);
    return res.data;
  },

  // Content: Biomarkers
  getBiomarkers: async (search?: string, category?: string) => {
    const query = new URLSearchParams();
    if (search) query.append('search', search);
    if (category) query.append('category', category);
    const url = `/admin/content/biomarkers${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  createBiomarker: async (data: {
    test_name: string;
    canonical_name: string;
    category?: string;
    default_unit?: string;
    ref_min?: number;
    ref_max?: number;
    critical_low?: number;
    critical_high?: number;
    description?: string;
  }) => {
    const res = await adminClient.post('/admin/content/biomarkers', data);
    return res.data;
  },

  updateBiomarker: async (refId: string, data: any) => {
    const res = await adminClient.patch(`/admin/content/biomarkers/${refId}`, data);
    return res.data;
  },

  deleteBiomarker: async (refId: string) => {
    const res = await adminClient.delete(`/admin/content/biomarkers/${refId}`);
    return res.data;
  },

  // Content: Glossary
  getGlossary: async (search?: string) => {
    const query = new URLSearchParams();
    if (search) query.append('search', search);
    const url = `/admin/content/glossary${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  createGlossary: async (data: { term: string; definition: string; reviewed_by?: string }) => {
    const res = await adminClient.post('/admin/content/glossary', data);
    return res.data;
  },

  updateGlossary: async (termId: string, data: { term?: string; definition?: string; reviewed_by?: string }) => {
    const res = await adminClient.patch(`/admin/content/glossary/${termId}`, data);
    return res.data;
  },

  deleteGlossary: async (termId: string) => {
    const res = await adminClient.delete(`/admin/content/glossary/${termId}`);
    return res.data;
  },

  // AI Review
  getAIReviews: async (statusFilter?: string) => {
    const query = new URLSearchParams();
    if (statusFilter) query.append('status_filter', statusFilter);
    const url = `/admin/ai-review/${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  reviewAIRecommendation: async (id: string, action: 'APPROVE' | 'FLAG' | 'OVERRIDE', overrideSpecialtyId?: string) => {
    const query = new URLSearchParams({ action });
    if (overrideSpecialtyId) query.append('override_specialty_id', overrideSpecialtyId);
    const res = await adminClient.patch(`/admin/ai-review/${id}?${query.toString()}`);
    return res.data;
  },

  // =================== DOCTOR PORTAL ===================
  getDoctorMe: async () => {
    const res = await adminClient.get('/doctor/me');
    return res.data;
  },

  getDoctorSchedule: async () => {
    const res = await adminClient.get('/doctor/schedule');
    return res.data;
  },

  setDoctorWorkingHours: async (workingHours: Array<{ day_of_week: number; start_time: string; end_time: string; slot_duration_minutes: number; is_active: boolean }>) => {
    const res = await adminClient.post('/doctor/schedule', { working_hours: workingHours });
    return res.data;
  },

  addScheduleBlock: async (data: { block_date: string; start_time?: string; end_time?: string; reason?: string }) => {
    const res = await adminClient.post('/doctor/schedule/block', data);
    return res.data;
  },

  removeScheduleBlock: async (blockId: string) => {
    const res = await adminClient.delete(`/doctor/schedule/block/${blockId}`);
    return res.data;
  },

  getDoctorAppointments: async (params?: { status?: string; start_date?: string; end_date?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    const url = `/doctor/appointments${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  updateDoctorAppointmentStatus: async (appointmentId: string, status: string, cancellationReason?: string) => {
    const res = await adminClient.patch(`/doctor/appointments/${appointmentId}/status`, {
      status,
      cancellation_reason: cancellationReason,
    });
    return res.data;
  },

  getDoctorAssignedPatients: async (search?: string) => {
    const query = new URLSearchParams();
    if (search) query.append('search', search);
    const url = `/doctor/patients${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await adminClient.get(url);
    return res.data;
  },

  getDoctorPatientChart: async (patientId: string) => {
    const res = await adminClient.get(`/doctor/patients/${patientId}`);
    return res.data;
  },

  saveConsultationNotes: async (appointmentId: string, data: { diagnosis?: string; clinical_notes: string; prescriptions?: string; follow_up_recommendation?: string }) => {
    const res = await adminClient.post(`/doctor/appointments/${appointmentId}/notes`, data);
    return res.data;
  },

  getConsultationNotes: async (appointmentId: string) => {
    const res = await adminClient.get(`/doctor/appointments/${appointmentId}/notes`);
    return res.data;
  },
};

