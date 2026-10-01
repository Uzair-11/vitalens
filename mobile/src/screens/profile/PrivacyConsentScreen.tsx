import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  Platform,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import {
  Shield,
  Download,
  Trash2,
  Sparkles,
  Compass,
  FileText,
  Bell,
  Heart,
  AlertCircle,
} from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { authApi } from '../../api/authApi';
import { COLORS } from '../../constants/colors';
import { useAuthStore } from '../../store/authStore';

export const PrivacyConsentScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [consents, setConsents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const logout = useAuthStore((state) => state.logout);

  const fetchConsents = async () => {
    try {
      const data = await authApi.getConsents();
      setConsents(data);
    } catch (e) {
      console.warn('Failed to load consents:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsents();
  }, []);

  const handleToggle = async (consentType: string, currentVal: boolean) => {
    try {
      const newVal = !currentVal;
      setConsents((prev) =>
        prev.map((c) => (c.consent_type === consentType ? { ...c, granted: newVal } : c))
      );
      await authApi.toggleConsent(consentType, newVal);
    } catch (e) {
      Alert.alert('Error', 'Failed to update consent preferences.');
      fetchConsents();
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const data = await authApi.exportData();
      const exportStr = JSON.stringify(data, null, 2);
      if (Platform.OS === 'web') {
        const blob = new Blob([exportStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `VitaLens_Data_Export_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        window.alert('Your complete medical data export has been downloaded.');
      } else {
        Alert.alert(
          'Data Export Generated',
          `Your complete profile, ${data.reports_count} reports, and ${data.appointments?.length || 0} appointments are packaged for export.`
        );
      }
    } catch (e) {
      Alert.alert('Export Error', 'Failed to export patient records.');
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAccount = () => {
    const doDelete = async () => {
      try {
        await authApi.deleteAccount();
        if (Platform.OS === 'web') {
          window.alert('Your account has been deactivated and scheduled for permanent erasure.');
        } else {
          Alert.alert('Account Deactivated', 'Your account has been scheduled for permanent erasure.');
        }
        await logout();
      } catch (e) {
        Alert.alert('Error', 'Failed to submit account deletion request.');
      }
    };

    if (Platform.OS === 'web') {
      if (window.confirm('Are you sure you want to request permanent erasure of your account and medical history? This action cannot be undone.')) {
        doDelete();
      }
    } else {
      Alert.alert(
        'Delete Account & Data',
        'Are you sure you want to request permanent erasure of your account and medical records? This action cannot be undone.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Delete My Data', style: 'destructive', onPress: doDelete },
        ]
      );
    }
  };

  const getConsentStatus = (type: string) => {
    const item = consents.find((c) => c.consent_type === type);
    return item ? item.granted : true;
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Privacy & Data Protection"
        subtitle="Manage your DPDP consents and patient data rights"
        onBack={() => navigation.goBack()}
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* DPDP Commitment Banner */}
        <View style={styles.banner}>
          <View style={styles.bannerIconCircle}>
            <Shield size={22} color={COLORS.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.bannerTitle}>Patient Data Sovereignty</Text>
            <Text style={styles.bannerText}>
              VitaLens enforces end-to-end user isolation, encrypted token storage, and granular consent boundaries in accordance with digital healthcare privacy principles.
            </Text>
          </View>
        </View>

        {loading ? (
          <ActivityIndicator size="large" color={COLORS.primary} style={{ marginVertical: 40 }} />
        ) : (
          <>
            {/* Consent Controls */}
            <Text style={styles.sectionHeader}>PROCESSING CONSENTS</Text>
            <Text style={styles.sectionSub}>Grant or revoke authorization for automated healthcare features.</Text>

            <View style={styles.card}>
              {/* 1. AI Report Analysis */}
              <View style={styles.consentRow}>
                <View style={[styles.consentIconBox, { backgroundColor: '#E0ECE7' }]}>
                  <Sparkles size={18} color={COLORS.primary} />
                </View>
                <View style={{ flex: 1, paddingRight: 12 }}>
                  <Text style={styles.consentTitle}>AI Report Analysis</Text>
                  <Text style={styles.consentDesc}>
                    Automated biomarker extraction, range validation, and plain-English medical summaries.
                  </Text>
                </View>
                <Switch
                  value={getConsentStatus('REPORT_ANALYSIS')}
                  onValueChange={() => handleToggle('REPORT_ANALYSIS', getConsentStatus('REPORT_ANALYSIS'))}
                  trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
                  thumbColor="#ffffff"
                />
              </View>

              <View style={styles.divider} />

              {/* 2. AI Specialty Navigation */}
              <View style={styles.consentRow}>
                <View style={[styles.consentIconBox, { backgroundColor: '#EFF6FF' }]}>
                  <Compass size={18} color="#2563EB" />
                </View>
                <View style={{ flex: 1, paddingRight: 12 }}>
                  <Text style={styles.consentTitle}>AI Specialty Navigation</Text>
                  <Text style={styles.consentDesc}>
                    Clinical matching of reported symptoms with appropriate specialist categories.
                  </Text>
                </View>
                <Switch
                  value={getConsentStatus('AI_PROCESSING')}
                  onValueChange={() => handleToggle('AI_PROCESSING', getConsentStatus('AI_PROCESSING'))}
                  trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
                  thumbColor="#ffffff"
                />
              </View>

              <View style={styles.divider} />

              {/* 3. Doctor Record Access */}
              <View style={styles.consentRow}>
                <View style={[styles.consentIconBox, { backgroundColor: '#F1F5F9' }]}>
                  <FileText size={18} color="#475569" />
                </View>
                <View style={{ flex: 1, paddingRight: 12 }}>
                  <Text style={styles.consentTitle}>Doctor Record Access</Text>
                  <Text style={styles.consentDesc}>
                    Allows verified consulting physicians to view your diagnostic lab reports.
                  </Text>
                </View>
                <Switch
                  value={getConsentStatus('DOCTOR_DATA_ACCESS')}
                  onValueChange={() => handleToggle('DOCTOR_DATA_ACCESS', getConsentStatus('DOCTOR_DATA_ACCESS'))}
                  trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
                  thumbColor="#ffffff"
                />
              </View>

              <View style={styles.divider} />

              {/* 4. Appointment Reminders */}
              <View style={styles.consentRow}>
                <View style={[styles.consentIconBox, { backgroundColor: '#FEF3C7' }]}>
                  <Bell size={18} color="#D97706" />
                </View>
                <View style={{ flex: 1, paddingRight: 12 }}>
                  <Text style={styles.consentTitle}>Appointment Reminders</Text>
                  <Text style={styles.consentDesc}>
                    Direct notifications for upcoming consultations and newly analyzed reports.
                  </Text>
                </View>
                <Switch
                  value={getConsentStatus('NOTIFICATIONS')}
                  onValueChange={() => handleToggle('NOTIFICATIONS', getConsentStatus('NOTIFICATIONS'))}
                  trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
                  thumbColor="#ffffff"
                />
              </View>

              <View style={styles.divider} />

              {/* 5. Health Insights & Updates */}
              <View style={styles.consentRow}>
                <View style={[styles.consentIconBox, { backgroundColor: '#FEE2E2' }]}>
                  <Heart size={18} color="#DC2626" />
                </View>
                <View style={{ flex: 1, paddingRight: 12 }}>
                  <Text style={styles.consentTitle}>Health Insights & Updates</Text>
                  <Text style={styles.consentDesc}>
                    Curated preventative wellness tips, dietary guidance, and feature updates.
                  </Text>
                </View>
                <Switch
                  value={getConsentStatus('MARKETING')}
                  onValueChange={() => handleToggle('MARKETING', getConsentStatus('MARKETING'))}
                  trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
                  thumbColor="#ffffff"
                />
              </View>
            </View>

            {/* Data Portability & Rights Section */}
            <Text style={styles.sectionHeader}>YOUR DATA RIGHTS</Text>
            <Text style={styles.sectionSub}>Exercise data portability or request complete erasure under DPDP compliance.</Text>

            <View style={styles.rightsContainer}>
              {/* Clean Secondary Outline Button: Export Medical Data */}
              <TouchableOpacity
                style={styles.exportOutlineBtn}
                onPress={handleExportData}
                disabled={exporting}
                activeOpacity={0.75}
              >
                {exporting ? (
                  <ActivityIndicator size="small" color={COLORS.primary} style={{ marginRight: 8 }} />
                ) : (
                  <Download size={18} color={COLORS.primary} style={{ marginRight: 8 }} />
                )}
                <Text style={styles.exportOutlineBtnText}>Export Complete Medical Data</Text>
              </TouchableOpacity>

              {/* Clean Red Outlined Button: Request Account Erasure */}
              <TouchableOpacity
                style={styles.deleteOutlineBtn}
                onPress={handleDeleteAccount}
                activeOpacity={0.75}
              >
                <Trash2 size={18} color="#DC2626" style={{ marginRight: 8 }} />
                <Text style={styles.deleteOutlineBtnText}>Request Account & Data Erasure</Text>
              </TouchableOpacity>
            </View>

            <View style={{ height: 32 }} />
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollArea: {
    flex: 1,
    paddingHorizontal: 20,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#EBF4F2',
    borderRadius: 18,
    padding: 16,
    marginVertical: 16,
    borderWidth: 1,
    borderColor: '#C6DDD8',
  },
  bannerIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#D1E6E1',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  bannerTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 4,
  },
  bannerText: {
    fontSize: 12,
    color: '#4A4A4A',
    lineHeight: 18,
  },
  sectionHeader: {
    fontSize: 12,
    fontWeight: '800',
    color: '#475569',
    letterSpacing: 0.8,
    marginBottom: 4,
    marginLeft: 4,
  },
  sectionSub: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 10,
    marginLeft: 4,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 20,
    boxShadow: '0px 2px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
  },
  consentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  consentIconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  consentTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#1E293B',
    marginBottom: 2,
  },
  consentDesc: {
    fontSize: 12,
    color: '#4A4A4A',
    lineHeight: 17,
  },
  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 6,
  },
  // Data Rights Buttons
  rightsContainer: {
    gap: 12,
    marginBottom: 16,
  },
  exportOutlineBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    borderRadius: 16,
    height: 50,
  },
  exportOutlineBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primary,
  },
  deleteOutlineBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEF2F2',
    borderWidth: 1.5,
    borderColor: '#FECACA',
    borderRadius: 16,
    height: 50,
  },
  deleteOutlineBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#DC2626',
  },
});
