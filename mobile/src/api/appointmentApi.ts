import { apiClient } from './client';
import { Appointment } from '../types';

export const appointmentApi = {
  bookAppointment: async (data: {
    doctor_id: string;
    appointment_date: string;
    appointment_time: string;
    report_id?: string;
    visit_reason?: string;
    patient_notes?: string;
  }): Promise<Appointment> => {
    const response = await apiClient.post('/appointments/', data);
    return response.data;
  },

  getAppointments: async (status?: string): Promise<Appointment[]> => {
    const response = await apiClient.get('/appointments/', {
      params: { status },
    });
    return response.data;
  },

  cancelAppointment: async (appointmentId: string, reason: string): Promise<Appointment> => {
    const response = await apiClient.patch(`/appointments/${appointmentId}/cancel`, {
      cancellation_reason: reason,
    });
    return response.data;
  },

  rescheduleAppointment: async (appointmentId: string, newDate: string, newTime: string): Promise<Appointment> => {
    const response = await apiClient.patch(`/appointments/${appointmentId}/reschedule`, {
      new_date: newDate,
      new_time: newTime,
    });
    return response.data;
  },
};
