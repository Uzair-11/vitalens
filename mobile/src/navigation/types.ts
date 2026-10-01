import { NavigatorScreenParams } from '@react-navigation/native';
import { SpecialtyRecommendationResult, Appointment } from '../types';

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type HomeStackParamList = {
  HomeScreen: undefined;
};

export type ReportsStackParamList = {
  ReportsList: undefined;
  UploadReport: undefined;
  ProcessingReport: { reportId: string };
  ReportAnalysis: { reportId: string };
  SymptomIntake: { reportId?: string };
  SpecialtyRecommendation: { recommendation?: SpecialtyRecommendationResult; reportId?: string };
  ReportQA: { reportId: string };
  BiomarkerTrends: undefined;
  ReportComparison: undefined;
};

export type DoctorsStackParamList = {
  DoctorList: { specialtyId?: string; specialtyName?: string } | undefined;
  DoctorProfile: { doctorId: string };
  SlotSelection: { doctorId: string };
  BookingSuccess: { appointment: Appointment };
};

export type AppointmentsStackParamList = {
  AppointmentsList: undefined;
};

export type ProfileStackParamList = {
  ProfileScreen: undefined;
  PersonalInformation: undefined;
  MedicalInformation: undefined;
  AccountSecurity: undefined;
  NotificationPreferences: undefined;
  PrivacyConsent: undefined;
  ClinicalDisclaimer: undefined;
};

export type AppTabParamList = {
  HomeTab: NavigatorScreenParams<HomeStackParamList>;
  ReportsTab: NavigatorScreenParams<ReportsStackParamList>;
  DoctorsTab: NavigatorScreenParams<DoctorsStackParamList>;
  AppointmentsTab: NavigatorScreenParams<AppointmentsStackParamList>;
  ProfileTab: NavigatorScreenParams<ProfileStackParamList>;
};

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  App: NavigatorScreenParams<AppTabParamList>;
};
