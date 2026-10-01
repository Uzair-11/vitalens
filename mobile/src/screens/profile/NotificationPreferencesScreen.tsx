import React, { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Switch,
  Alert,
  StyleSheet,
  ActivityIndicator,
  Platform,
} from 'react-native';
import {
  Bell,
  MessageSquare,
  Mail,
  Calendar,
  FileText,
  Sparkles,
  Heart,
  CheckCircle2,
  Clock,
  Save,
  AlertCircle,
} from 'lucide-react-native';
import * as SecureStore from 'expo-secure-store';
import { Header } from '../../components/common/Header';
import { COLORS } from '../../constants/colors';

const STORAGE_KEY = 'vitalens_notification_preferences';
const isWeb = Platform.OS === 'web';

const storage = {
  getItem: async (key: string): Promise<string | null> => {
    if (isWeb) {
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          return window.localStorage.getItem(key);
        }
      } catch (e) {
        console.warn('localStorage get error:', e);
      }
      return null;
    } else {
      try {
        return await SecureStore.getItemAsync(key);
      } catch (e) {
        console.warn('SecureStore get error:', e);
        return null;
      }
    }
  },
  setItem: async (key: string, value: string): Promise<void> => {
    if (isWeb) {
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          window.localStorage.setItem(key, value);
        }
      } catch (e) {
        console.warn('localStorage set error:', e);
      }
    } else {
      try {
        await SecureStore.setItemAsync(key, value);
      } catch (e) {
        console.warn('SecureStore set error:', e);
      }
    }
  },
};

export const NotificationPreferencesScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  // Delivery Channels
  const [pushEnabled, setPushEnabled] = useState(true);
  const [smsEnabled, setSmsEnabled] = useState(true);
  const [emailEnabled, setEmailEnabled] = useState(false);

  // Appointments
  const [apptReminders, setApptReminders] = useState(true);
  const [apptUpdates, setApptUpdates] = useState(true);

  // Reports & Lab Insights
  const [reportUploaded, setReportUploaded] = useState(true);
  const [labInsightsReady, setLabInsightsReady] = useState(true);
  const [criticalBiomarkers, setCriticalBiomarkers] = useState(true);

  // Wellness & Summaries
  const [healthTips, setHealthTips] = useState(false);
  const [medicationNudges, setMedicationNudges] = useState(true);

  const [saving, setSaving] = useState(false);
  const [savedBanner, setSavedBanner] = useState(false);

  // Load saved prefs
  useEffect(() => {
    (async () => {
      try {
        const raw = await storage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          setPushEnabled(parsed.pushEnabled ?? true);
          setSmsEnabled(parsed.smsEnabled ?? true);
          setEmailEnabled(parsed.emailEnabled ?? false);
          setApptReminders(parsed.apptReminders ?? true);
          setApptUpdates(parsed.apptUpdates ?? true);
          setReportUploaded(parsed.reportUploaded ?? true);
          setLabInsightsReady(parsed.labInsightsReady ?? true);
          setCriticalBiomarkers(parsed.criticalBiomarkers ?? true);
          setHealthTips(parsed.healthTips ?? false);
          setMedicationNudges(parsed.medicationNudges ?? true);
        }
      } catch (e) {
        console.warn('Failed to load notification prefs:', e);
      }
    })();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const prefs = {
        pushEnabled,
        smsEnabled,
        emailEnabled,
        apptReminders,
        apptUpdates,
        reportUploaded,
        labInsightsReady,
        criticalBiomarkers,
        healthTips,
        medicationNudges,
      };
      await storage.setItem(STORAGE_KEY, JSON.stringify(prefs));
      setSavedBanner(true);
      setTimeout(() => {
        setSavedBanner(false);
      }, 3000);
    } catch (e) {
      Alert.alert('Error', 'Failed to save notification preferences.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Notifications"
        subtitle="Granular delivery channels & alert categories"
        onBack={() => navigation.goBack()}
      />

      <ScrollView
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {savedBanner && (
          <View style={styles.successBanner}>
            <CheckCircle2 size={16} color={COLORS.success} style={{ marginRight: 8 }} />
            <Text style={styles.successBannerText}>Notification preferences updated successfully!</Text>
          </View>
        )}

        {/* Channels Section */}
        <Text style={styles.sectionHeader}>NOTIFICATION CHANNELS</Text>
        <Text style={styles.sectionSub}>Choose how you receive health alerts & reminders.</Text>

        <View style={styles.card}>
          {/* Push Notifications */}
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#DEF7EC' }]}>
              <Bell size={20} color="#059669" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Push Notifications</Text>
              <Text style={styles.settingSubtitle}>Instant alerts directly on your device lock screen.</Text>
            </View>
            <Switch
              value={pushEnabled}
              onValueChange={setPushEnabled}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          {/* SMS Messages */}
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#EFF6FF' }]}>
              <MessageSquare size={20} color="#2563EB" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>SMS Text Messages</Text>
              <Text style={styles.settingSubtitle}>Critical reminders sent to your verified +91 mobile number.</Text>
            </View>
            <Switch
              value={smsEnabled}
              onValueChange={setSmsEnabled}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          {/* Email Digests */}
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#FEF3C7' }]}>
              <Mail size={20} color="#D97706" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Email Digests</Text>
              <Text style={styles.settingSubtitle}>Detailed report breakdowns & appointment receipts.</Text>
            </View>
            <Switch
              value={emailEnabled}
              onValueChange={setEmailEnabled}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>
        </View>

        {/* Category 1: Appointments */}
        <Text style={styles.sectionHeader}>APPOINTMENTS & DOCTORS</Text>
        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#F1F5F9' }]}>
              <Clock size={20} color="#475569" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Reminders (24 hours before)</Text>
              <Text style={styles.settingSubtitle}>Advance notice so you never miss a scheduled consultation.</Text>
            </View>
            <Switch
              value={apptReminders}
              onValueChange={setApptReminders}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#E0ECE7' }]}>
              <Calendar size={20} color={COLORS.primary} />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Schedule & Reschedule Updates</Text>
              <Text style={styles.settingSubtitle}>Instant alerts if a doctor confirms, delays, or reschedules.</Text>
            </View>
            <Switch
              value={apptUpdates}
              onValueChange={setApptUpdates}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>
        </View>

        {/* Category 2: Medical Reports & Lab Insights */}
        <Text style={styles.sectionHeader}>MEDICAL REPORTS & LAB INSIGHTS</Text>
        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#EFF6FF' }]}>
              <FileText size={20} color="#2563EB" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>New Report Uploaded</Text>
              <Text style={styles.settingSubtitle}>Notification when your PDF or scanned report finishes uploading.</Text>
            </View>
            <Switch
              value={reportUploaded}
              onValueChange={setReportUploaded}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#E0ECE7' }]}>
              <Sparkles size={20} color={COLORS.primary} />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Lab Insights & Triage Ready</Text>
              <Text style={styles.settingSubtitle}>Alert when AI extraction and biomarker summaries are complete.</Text>
            </View>
            <Switch
              value={labInsightsReady}
              onValueChange={setLabInsightsReady}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#FEE2E2' }]}>
              <AlertCircle size={20} color="#DC2626" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Critical Biomarker Alerts</Text>
              <Text style={styles.settingSubtitle}>High-priority notification if any biomarker requires urgent doctor review.</Text>
            </View>
            <Switch
              value={criticalBiomarkers}
              onValueChange={setCriticalBiomarkers}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>
        </View>

        {/* Category 3: Wellness & Summaries */}
        <Text style={styles.sectionHeader}>WELLNESS & MARKETING</Text>
        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#FEF3C7' }]}>
              <Heart size={20} color="#D97706" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Health Tips & Weekly Summaries</Text>
              <Text style={styles.settingSubtitle}>Curated dietary guidelines, sleep tips & lab trend recaps.</Text>
            </View>
            <Switch
              value={healthTips}
              onValueChange={setHealthTips}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#F1F5F9' }]}>
              <Clock size={20} color="#475569" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Routine & Hydration Nudges</Text>
              <Text style={styles.settingSubtitle}>Subtle reminders for water intake, medication, and movement.</Text>
            </View>
            <Switch
              value={medicationNudges}
              onValueChange={setMedicationNudges}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>
        </View>

        {/* Save Preferences Button */}
        <TouchableOpacity
          onPress={handleSave}
          disabled={saving}
          style={styles.saveBtn}
          activeOpacity={0.8}
        >
          {saving ? (
            <ActivityIndicator color="#ffffff" size="small" />
          ) : (
            <>
              <Save size={18} color="#ffffff" style={{ marginRight: 8 }} />
              <Text style={styles.saveBtnText}>Save Notification Preferences</Text>
            </>
          )}
        </TouchableOpacity>

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
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 32,
  },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DEF7EC',
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#BCF0DA',
  },
  successBannerText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#03543F',
    flex: 1,
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
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 20,
    boxShadow: '0px 2px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  settingIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  settingTextContainer: {
    flex: 1,
    paddingRight: 12,
  },
  settingTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#1E293B',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 12,
    color: '#4A4A4A',
    lineHeight: 17,
  },
  divider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 12,
  },
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    height: 52,
    boxShadow: '0px 3px 6px rgba(15, 92, 94, 0.25)',
    elevation: 2,
    marginTop: 4,
  },
  saveBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
});
