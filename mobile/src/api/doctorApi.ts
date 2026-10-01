import { apiClient } from './client';
import { Specialty, Doctor, DoctorSlot } from '../types';

export const doctorApi = {
  getSpecialties: async (): Promise<Specialty[]> => {
    const response = await apiClient.get('/doctors/specialties');
    return response.data;
  },

  searchDoctors: async (params?: {
    specialty_id?: string;
    city?: string;
    max_fee?: number;
    min_rating?: number;
    sort_by?: string;
  }): Promise<Doctor[]> => {
    const response = await apiClient.get('/doctors/', { params });
    return response.data;
  },

  getDoctorDetail: async (doctorId: string): Promise<Doctor> => {
    const response = await apiClient.get(`/doctors/${doctorId}`);
    return response.data;
  },

  getDoctorAvailability: async (doctorId: string, startDate?: string, endDate?: string): Promise<DoctorSlot[]> => {
    const response = await apiClient.get(`/doctors/${doctorId}/availability`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },
};
