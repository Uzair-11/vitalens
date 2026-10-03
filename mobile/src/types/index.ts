export interface User {
  id: string;
  email: string;
  full_name: string;
  role?: string;
  phone?: string;
  date_of_birth?: string;
  biological_sex?: string;
  blood_group?: string;
  emergency_contact?: string;
  avatar_url?: string;
  abha_number?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  is_verified?: boolean;
  email_verified?: boolean;
  phone_verified?: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  date_of_birth?: string;
}

export interface Biomarker {
  id?: string;
  test_name: string;
  canonical_name: string;
  value_numeric?: number;
  value_text?: string;
  unit?: string;
  reference_min?: number;
  reference_max?: number;
  reference_text?: string;
  flag: 'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL' | 'CRITICAL_HIGH' | 'CRITICAL_LOW' | 'ABNORMAL' | string;
  category: string;
  clinical_interpretation?: string;
}

export interface GlossaryItem {
  term: string;
  definition: string;
}

export interface ReportAnalysis {
  id?: string;
  plain_summary: string;
  terminology_glossary: GlossaryItem[];
  clinical_disclaimer: string;
  generated_at?: string;
}

export interface MedicalReportSummary {
  id: string;
  file_name: string;
  report_type: string;
  report_date: string;
  status: 'PENDING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  biomarker_count: number;
  abnormal_count: number;
}

export interface MedicalReportDetail {
  id: string;
  file_name: string;
  report_type: string;
  report_date: string;
  status: 'PENDING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  biomarkers: Biomarker[];
  analysis?: ReportAnalysis;
}

export interface Specialty {
  id: string;
  name: string;
  description?: string;
  icon_name?: string;
}

export interface Doctor {
  id: string;
  specialty_id: string;
  specialty_name?: string;
  full_name: string;
  qualification: string;
  experience_years: number;
  clinic_name: string;
  address: string;
  city: string;
  consultation_fee: number;
  rating: number;
  review_count: number;
  profile_photo_url?: string;
  languages: string[];
  bio?: string;
  available_slots_count?: number;
  next_available_slot?: string;
}

export interface DoctorSlot {
  id: string;
  doctor_id: string;
  available_date: string;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  is_booked: boolean;
}

export interface Appointment {
  id: string;
  user_id: string;
  doctor_id: string;
  doctor_name?: string;
  doctor_specialty?: string;
  doctor_clinic?: string;
  doctor_address?: string;
  doctor_photo?: string;
  consultation_fee?: number;
  report_id?: string;
  report_name?: string;
  appointment_date: string;
  appointment_time: string;
  status: 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'RESCHEDULED';
  visit_reason?: string;
  patient_notes?: string;
  cancellation_reason?: string;
  created_at: string;
}

export interface SpecialtyRecommendationResult {
  recommended_specialty_id: string;
  recommended_specialty_name: string;
  confidence_score: number;
  rationale: string;
  is_emergency_flagged: boolean;
  emergency_message?: string;
  abnormal_biomarkers_considered: string[];
  symptoms_considered: string[];
}

export interface TrendDataPoint {
  date: string;
  value: number;
  unit: string;
  flag: string;
  reference_min?: number;
  reference_max?: number;
  report_id: string;
}

export interface BiomarkerTrendSeries {
  canonical_name: string;
  category: string;
  data_points: TrendDataPoint[];
}

export interface ComparisonItem {
  canonical_name: string;
  test_name: string;
  unit: string;
  report_1_value?: number;
  report_1_flag?: string;
  report_2_value?: number;
  report_2_flag?: string;
  delta?: number;
  status_change: 'IMPROVED' | 'WORSENED' | 'STABLE' | 'CHANGED' | 'NEW';
  explanation: string;
}

export interface ReportComparisonData {
  report_1_id: string;
  report_1_date: string;
  report_2_id: string;
  report_2_date: string;
  items: ComparisonItem[];
  clinical_disclaimer: string;
}
