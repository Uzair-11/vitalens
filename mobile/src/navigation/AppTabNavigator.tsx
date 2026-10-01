import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Home, FileText, Stethoscope, Calendar, User as UserIcon } from 'lucide-react-native';
import {
  AppTabParamList,
  HomeStackParamList,
  ReportsStackParamList,
  DoctorsStackParamList,
  AppointmentsStackParamList,
  ProfileStackParamList,
} from './types';

// Screens
import { HomeScreen } from '../screens/home/HomeScreen';
import { ReportsListScreen } from '../screens/reports/ReportsListScreen';
import { UploadReportScreen } from '../screens/reports/UploadReportScreen';
import { ProcessingReportScreen } from '../screens/reports/ProcessingReportScreen';
import { ReportAnalysisScreen } from '../screens/reports/ReportAnalysisScreen';
import { SymptomIntakeScreen } from '../screens/reports/SymptomIntakeScreen';
import { SpecialtyRecommendationScreen } from '../screens/reports/SpecialtyRecommendationScreen';
import { ReportQAScreen } from '../screens/reports/ReportQAScreen';
import { BiomarkerTrendsScreen } from '../screens/reports/BiomarkerTrendsScreen';
import { ReportComparisonScreen } from '../screens/reports/ReportComparisonScreen';

import { DoctorListScreen } from '../screens/doctors/DoctorListScreen';
import { DoctorProfileScreen } from '../screens/doctors/DoctorProfileScreen';
import { SlotSelectionScreen } from '../screens/doctors/SlotSelectionScreen';
import { BookingSuccessScreen } from '../screens/doctors/BookingSuccessScreen';

import { AppointmentsListScreen } from '../screens/appointments/AppointmentsListScreen';
import { ProfileScreen } from '../screens/profile/ProfileScreen';
import { ClinicalDisclaimerScreen } from '../screens/profile/ClinicalDisclaimerScreen';
import { COLORS } from '../constants/colors';

const Tab = createBottomTabNavigator<AppTabParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const ReportsStack = createNativeStackNavigator<ReportsStackParamList>();
const DoctorsStack = createNativeStackNavigator<DoctorsStackParamList>();
const AppointmentsStack = createNativeStackNavigator<AppointmentsStackParamList>();
const ProfileStack = createNativeStackNavigator<ProfileStackParamList>();

const HomeNavigator = () => (
  <HomeStack.Navigator screenOptions={{ headerShown: false }}>
    <HomeStack.Screen name="HomeScreen" component={HomeScreen} />
  </HomeStack.Navigator>
);

const ReportsNavigator = () => (
  <ReportsStack.Navigator screenOptions={{ headerShown: false }}>
    <ReportsStack.Screen name="ReportsList" component={ReportsListScreen} />
    <ReportsStack.Screen name="UploadReport" component={UploadReportScreen} />
    <ReportsStack.Screen name="ProcessingReport" component={ProcessingReportScreen} />
    <ReportsStack.Screen name="ReportAnalysis" component={ReportAnalysisScreen} />
    <ReportsStack.Screen name="SymptomIntake" component={SymptomIntakeScreen} />
    <ReportsStack.Screen name="SpecialtyRecommendation" component={SpecialtyRecommendationScreen} />
    <ReportsStack.Screen name="ReportQA" component={ReportQAScreen} />
    <ReportsStack.Screen name="BiomarkerTrends" component={BiomarkerTrendsScreen} />
    <ReportsStack.Screen name="ReportComparison" component={ReportComparisonScreen} />
  </ReportsStack.Navigator>
);

const DoctorsNavigator = () => (
  <DoctorsStack.Navigator screenOptions={{ headerShown: false }}>
    <DoctorsStack.Screen name="DoctorList" component={DoctorListScreen} />
    <DoctorsStack.Screen name="DoctorProfile" component={DoctorProfileScreen} />
    <DoctorsStack.Screen name="SlotSelection" component={SlotSelectionScreen} />
    <DoctorsStack.Screen name="BookingSuccess" component={BookingSuccessScreen} />
  </DoctorsStack.Navigator>
);

const AppointmentsNavigator = () => (
  <AppointmentsStack.Navigator screenOptions={{ headerShown: false }}>
    <AppointmentsStack.Screen name="AppointmentsList" component={AppointmentsListScreen} />
  </AppointmentsStack.Navigator>
);

import { PrivacyConsentScreen } from '../screens/profile/PrivacyConsentScreen';
import { PersonalInformationScreen } from '../screens/profile/PersonalInformationScreen';
import { MedicalInformationScreen } from '../screens/profile/MedicalInformationScreen';
import { AccountSecurityScreen } from '../screens/profile/AccountSecurityScreen';
import { NotificationPreferencesScreen } from '../screens/profile/NotificationPreferencesScreen';

const ProfileNavigator = () => (
  <ProfileStack.Navigator screenOptions={{ headerShown: false }}>
    <ProfileStack.Screen name="ProfileScreen" component={ProfileScreen} />
    <ProfileStack.Screen name="PersonalInformation" component={PersonalInformationScreen} />
    <ProfileStack.Screen name="MedicalInformation" component={MedicalInformationScreen} />
    <ProfileStack.Screen name="AccountSecurity" component={AccountSecurityScreen} />
    <ProfileStack.Screen name="NotificationPreferences" component={NotificationPreferencesScreen} />
    <ProfileStack.Screen name="PrivacyConsent" component={PrivacyConsentScreen} />
    <ProfileStack.Screen name="ClinicalDisclaimer" component={ClinicalDisclaimerScreen} />
  </ProfileStack.Navigator>
);

export const AppTabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textMuted,
        tabBarStyle: {
          backgroundColor: COLORS.surface,
          borderTopColor: COLORS.borderSubtle,
          borderTopWidth: 1,
          elevation: 8,
          boxShadow: '0px -2px 6px rgba(38, 51, 52, 0.04)',
          paddingTop: 8,
          height: 64,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '700',
          paddingBottom: 8,
          letterSpacing: 0.2,
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeNavigator}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({ color, size }) => <Home size={size - 2} color={color} strokeWidth={2.2} />,
        }}
      />
      <Tab.Screen
        name="ReportsTab"
        component={ReportsNavigator}
        options={{
          tabBarLabel: 'Reports',
          tabBarIcon: ({ color, size }) => <FileText size={size - 2} color={color} strokeWidth={2.2} />,
        }}
      />
      <Tab.Screen
        name="DoctorsTab"
        component={DoctorsNavigator}
        options={{
          tabBarLabel: 'Doctors',
          tabBarIcon: ({ color, size }) => <Stethoscope size={size - 2} color={color} strokeWidth={2.2} />,
        }}
      />
      <Tab.Screen
        name="AppointmentsTab"
        component={AppointmentsNavigator}
        options={{
          tabBarLabel: 'Appointments',
          tabBarIcon: ({ color, size }) => <Calendar size={size - 2} color={color} strokeWidth={2.2} />,
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileNavigator}
        options={{
          tabBarLabel: 'Profile',
          tabBarIcon: ({ color, size }) => <UserIcon size={size - 2} color={color} strokeWidth={2.2} />,
        }}
      />
    </Tab.Navigator>
  );
};
