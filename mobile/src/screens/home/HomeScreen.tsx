import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  StyleSheet,
  Image,
} from 'react-native';
import {
  UploadCloud,
  FileText,
  Calendar,
  Stethoscope,
  ChevronRight,
  ArrowRight,
  Sparkles,
  AlertCircle,
  CheckCircle,
} from 'lucide-react-native';
import { useAuthStore } from '../../store/authStore';
import { reportApi } from '../../api/reportApi';
import { appointmentApi } from '../../api/appointmentApi';
import { MedicalReportSummary, Appointment } from '../../types';
import { DisclaimerCard } from '../../components/common/DisclaimerCard';
import { useReportWizardStore } from '../../store/reportWizardStore';
import { COLORS } from '../../constants/colors';
import { getMediaUrl } from '../../constants/config';

export const HomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const user = useAuthStore((state) => state.user);
  const resetWizard = useReportWizardStore((state) => state.resetWizard);
  const [reports, setReports] = useState<MedicalReportSummary[]>([]);
  const [upcomingAppt, setUpcomingAppt] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboardData = async () => {
    try {
      const [reportsData, apptsData] = await Promise.all([
        reportApi.getAllReports(),
        appointmentApi.getAppointments('CONFIRMED'),
      ]);
      setReports(reportsData);
      setUpcomingAppt(apptsData.length > 0 ? apptsData[0] : null);
    } catch (e) {
      console.warn('Dashboard load error:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleUploadPress = () => {
    resetWizard();
    navigation.navigate('ReportsTab', { screen: 'UploadReport' });
  };

  const getGreetingTime = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const firstName = user?.full_name?.split(' ')[0] || 'Uzair';
  const avatarUrl = getMediaUrl(user?.avatar_url);
  const latestReport = reports.length > 0 ? reports[0] : null;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            tintColor={COLORS.primary}
            colors={[COLORS.primary]}
            onRefresh={() => {
              setRefreshing(true);
              loadDashboardData();
            }}
          />
        }
        contentContainerStyle={styles.scrollContent}
      >
        {/* Header: Greeting & Avatar */}
        <View style={styles.headerRow}>
          <View style={{ flex: 1, marginRight: 12 }}>
            <Text style={styles.greetingTitle}>
              {getGreetingTime()}, {firstName}
            </Text>
            <Text style={styles.greetingSubtitle}>
              Let's make your health report easier to understand.
            </Text>
          </View>
          <TouchableOpacity
            onPress={() => navigation.navigate('ProfileTab')}
            activeOpacity={0.8}
            style={styles.avatarButton}
          >
            {avatarUrl ? (
              <Image source={{ uri: avatarUrl }} style={styles.avatarCircle} />
            ) : (
              <View style={styles.avatarCircle}>
                <Text style={styles.avatarLetter}>{firstName.charAt(0).toUpperCase()}</Text>
              </View>
            )}
          </TouchableOpacity>
        </View>

        {/* Primary Feature Hero Card: Deep Teal */}
        <View style={styles.heroCard}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
            <View style={styles.heroBadge}>
              <Sparkles size={13} color="#ffffff" style={{ marginRight: 5 }} />
              <Text style={styles.heroBadgeText}>AI Report Comprehension</Text>
            </View>
            <Image
              source={require('../../../assets/images/vitalens-icon.png')}
              style={{ width: 36, height: 36, opacity: 0.85 }}
              resizeMode="contain"
            />
          </View>
          <Text style={styles.heroHeading}>Have a medical report?</Text>
          <Text style={styles.heroSubheading}>
            Upload it and let us explain what's inside in clear, simple language.
          </Text>

          <TouchableOpacity
            onPress={handleUploadPress}
            activeOpacity={0.9}
            style={styles.heroCtaBtn}
          >
            <UploadCloud size={18} color={COLORS.primaryDark} style={{ marginRight: 8 }} />
            <Text style={styles.heroCtaText}>Upload Report</Text>
          </TouchableOpacity>
        </View>

        {/* Quick Action Navigation Pills */}
        <View style={styles.quickPillsRow}>
          <TouchableOpacity
            onPress={() => navigation.navigate('ReportsTab', { screen: 'ReportsList' })}
            style={styles.quickPill}
            activeOpacity={0.8}
          >
            <FileText size={15} color={COLORS.primary} style={{ marginRight: 6 }} />
            <Text style={styles.quickPillText}>My Reports</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => navigation.navigate('DoctorsTab', { screen: 'DoctorList' })}
            style={styles.quickPill}
            activeOpacity={0.8}
          >
            <Stethoscope size={15} color={COLORS.primary} style={{ marginRight: 6 }} />
            <Text style={styles.quickPillText}>Find Doctor</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => navigation.navigate('AppointmentsTab')}
            style={styles.quickPill}
            activeOpacity={0.8}
          >
            <Calendar size={15} color={COLORS.primary} style={{ marginRight: 6 }} />
            <Text style={styles.quickPillText}>Appointments</Text>
          </TouchableOpacity>
        </View>

        {/* Recent Report Section */}
        <View style={styles.sectionBlock}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Report</Text>
            {reports.length > 1 && (
              <TouchableOpacity onPress={() => navigation.navigate('ReportsTab', { screen: 'ReportsList' })}>
                <Text style={styles.sectionActionText}>View All ({reports.length})</Text>
              </TouchableOpacity>
            )}
          </View>

          {loading ? (
            <ActivityIndicator size="small" color={COLORS.primary} style={{ marginVertical: 18 }} />
          ) : latestReport ? (
            <View style={styles.recentReportCard}>
              <View style={styles.reportCardTop}>
                <View style={styles.reportIconCircle}>
                  <FileText size={20} color={COLORS.primary} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.reportCardName} numberOfLines={1}>
                    {latestReport.file_name}
                  </Text>
                  <Text style={styles.reportCardDate}>{latestReport.report_date}</Text>
                </View>

                {latestReport.abnormal_count > 0 ? (
                  <View style={styles.attentionBadge}>
                    <AlertCircle size={12} color={COLORS.urgent} style={{ marginRight: 4 }} />
                    <Text style={styles.attentionBadgeText}>
                      {latestReport.abnormal_count} values outside range
                    </Text>
                  </View>
                ) : (
                  <View style={styles.normalBadge}>
                    <CheckCircle size={12} color={COLORS.normal} style={{ marginRight: 4 }} />
                    <Text style={styles.normalBadgeText}>Within range</Text>
                  </View>
                )}
              </View>

              <View style={styles.reportCardFooter}>
                <Text style={styles.biomarkerCountText}>
                  {latestReport.biomarker_count} biomarkers evaluated
                </Text>
                <TouchableOpacity
                  onPress={() => {
                    navigation.navigate('ReportsTab', {
                      screen: 'ReportAnalysis',
                      params: { reportId: latestReport.id },
                    });
                  }}
                  style={styles.viewAnalysisBtn}
                  activeOpacity={0.8}
                >
                  <Text style={styles.viewAnalysisBtnText}>View Analysis</Text>
                  <ArrowRight size={14} color={COLORS.primary} style={{ marginLeft: 4 }} />
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyCardTitle}>No reports yet</Text>
              <Text style={styles.emptyCardBody}>
                Upload your first medical report to start understanding your results and tracking your health.
              </Text>
            </View>
          )}
        </View>

        {/* Upcoming Appointment Section */}
        {upcomingAppt && (
          <View style={styles.sectionBlock}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Upcoming Appointment</Text>
              <TouchableOpacity onPress={() => navigation.navigate('AppointmentsTab')}>
                <Text style={styles.sectionActionText}>View Details</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.apptCard}>
              <View style={styles.apptHeaderRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.apptDocName}>{upcomingAppt.doctor_name}</Text>
                  <Text style={styles.apptDocSpec}>{upcomingAppt.doctor_specialty}</Text>
                </View>
                <View style={styles.apptScheduleBadge}>
                  <Text style={styles.apptScheduleText}>{upcomingAppt.appointment_date}</Text>
                </View>
              </View>

              <View style={styles.apptFooterRow}>
                <Text style={styles.apptClinicText}>{upcomingAppt.doctor_clinic}</Text>
                <Text style={styles.apptTimeText}>{upcomingAppt.appointment_time}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Clinical Disclaimer */}
        <DisclaimerCard />
        <View style={{ height: 20 }} />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    padding: 20,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
    marginTop: 4,
  },
  greetingTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.textPrimary,
    letterSpacing: -0.4,
  },
  greetingSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 3,
    lineHeight: 18,
  },
  avatarButton: {
    padding: 2,
  },
  avatarCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.secondaryLight,
    borderWidth: 1.5,
    borderColor: COLORS.secondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarLetter: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.primaryDark,
  },
  heroCard: {
    backgroundColor: COLORS.primary,
    borderRadius: 24,
    padding: 24,
    marginBottom: 18,
    boxShadow: '0px 6px 10px rgba(18, 54, 45, 0.2)',
    elevation: 4,
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.16)',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  heroBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: 0.2,
  },
  heroHeading: {
    fontSize: 21,
    fontWeight: '800',
    color: '#ffffff',
    letterSpacing: -0.3,
    marginBottom: 6,
  },
  heroSubheading: {
    fontSize: 13,
    color: '#D2E3E3',
    lineHeight: 19,
    marginBottom: 18,
  },
  heroCtaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 14,
    paddingVertical: 13,
    paddingHorizontal: 20,
    alignSelf: 'flex-start',
    boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
    elevation: 2,
  },
  heroCtaText: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.primaryDark,
  },
  quickPillsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
    marginBottom: 22,
  },
  quickPill: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 1px 4px rgba(38, 51, 52, 0.03)',
    elevation: 1,
  },
  quickPillText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  sectionBlock: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textPrimary,
    letterSpacing: -0.2,
  },
  sectionActionText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
  },
  recentReportCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
  },
  reportCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  reportIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  reportCardName: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  reportCardDate: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  attentionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.urgentLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#F4C5BF',
  },
  attentionBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.urgent,
  },
  normalBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.normalLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#BEE0D0',
  },
  normalBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.normal,
  },
  reportCardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  biomarkerCountText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  viewAnalysisBtn: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewAnalysisBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primary,
  },
  apptCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
  },
  apptHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  apptDocName: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  apptDocSpec: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
    marginTop: 2,
  },
  apptScheduleBadge: {
    backgroundColor: COLORS.primaryLight,
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 8,
  },
  apptScheduleText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  apptFooterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  apptClinicText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  apptTimeText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  emptyCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  emptyCardTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  emptyCardBody: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 17,
  },
});
