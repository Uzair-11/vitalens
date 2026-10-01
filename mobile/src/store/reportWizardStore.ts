import { create } from 'zustand';
import { MedicalReportDetail, SpecialtyRecommendationResult, Doctor, DoctorSlot } from '../types';

interface ReportWizardState {
  activeReport: MedicalReportDetail | null;
  activeSymptomLogId: string | null;
  activeRecommendation: SpecialtyRecommendationResult | null;
  selectedDoctor: Doctor | null;
  selectedSlot: DoctorSlot | null;
  
  setActiveReport: (report: MedicalReportDetail | null) => void;
  setActiveSymptomLogId: (id: string | null) => void;
  setActiveRecommendation: (rec: SpecialtyRecommendationResult | null) => void;
  setSelectedDoctor: (doctor: Doctor | null) => void;
  setSelectedSlot: (slot: DoctorSlot | null) => void;
  resetWizard: () => void;
}

export const useReportWizardStore = create<ReportWizardState>((set) => ({
  activeReport: null,
  activeSymptomLogId: null,
  activeRecommendation: null,
  selectedDoctor: null,
  selectedSlot: null,

  setActiveReport: (report) => set({ activeReport: report }),
  setActiveSymptomLogId: (id) => set({ activeSymptomLogId: id }),
  setActiveRecommendation: (rec) => set({ activeRecommendation: rec }),
  setSelectedDoctor: (doctor) => set({ selectedDoctor: doctor }),
  setSelectedSlot: (slot) => set({ selectedSlot: slot }),
  resetWizard: () => set({
    activeReport: null,
    activeSymptomLogId: null,
    activeRecommendation: null,
    selectedDoctor: null,
    selectedSlot: null
  }),
}));
