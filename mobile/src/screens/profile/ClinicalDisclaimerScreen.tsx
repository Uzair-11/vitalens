import React, { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Check,
  Clock,
  Sparkles,
  ArrowRight,
} from 'lucide-react-native';
import * as SecureStore from 'expo-secure-store';
import { Header } from '../../components/common/Header';
import { COLORS } from '../../constants/colors';

const STORAGE_KEY = 'vitalens_clinical_safety_ack_v1';
const CURRENT_NOTICE_VERSION = '1.4 (Sept 2026)';
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

export const ClinicalDisclaimerScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [acknowledged, setAcknowledged] = useState(false);
  const [ackDate, setAckDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const raw = await storage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed.acknowledged) {
            setAcknowledged(true);
            setAckDate(parsed.timestamp ? new Date(parsed.timestamp).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            }) : 'Active');
          }
        }
      } catch (e) {
        console.warn('Error reading clinical safety acknowledgment:', e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleAcknowledge = async () => {
    setSaving(true);
    try {
      const payload = {
        acknowledged: true,
        version: CURRENT_NOTICE_VERSION,
        timestamp: new Date().toISOString(),
      };
      await storage.setItem(STORAGE_KEY, JSON.stringify(payload));
      setAcknowledged(true);
      setAckDate('Just now');

      Alert.alert(
        'Notice Acknowledged',
        'You have confirmed and accepted the VitaLens Clinical Safety Guidelines.',
        [
          {
            text: 'Return to Profile',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (e) {
      Alert.alert('Error', 'Unable to record acknowledgment. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      {/* Clean Header with back button only (no floating gear) */}
      <Header
        title="Clinical Safety Notice"
        subtitle="Medical scope & regulatory safeguards"
        onBack={() => navigation.goBack()}
      />

      {/* Main Scroll Container with clean clipping beneath header */}
      <ScrollView
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Acknowledgment Status Pill (if already accepted) */}
        {acknowledged && (
          <View style={styles.ackBanner}>
            <CheckCircle2 size={15} color="#059669" style={{ marginRight: 8 }} />
            <Text style={styles.ackBannerText}>
              Acknowledged on {ackDate || 'Current Session'} • Version {CURRENT_NOTICE_VERSION}
            </Text>
          </View>
        )}

        {/* Hero Scope Card */}
        <View style={styles.heroCard}>
          <View style={styles.heroTopRow}>
            <View style={styles.heroIconBox}>
              <ShieldCheck size={22} color={COLORS.primaryDark} />
            </View>
            <View style={styles.complianceBadge}>
              <Text style={styles.complianceBadgeText}>REGULATORY NOTICE</Text>
            </View>
          </View>

          <Text style={styles.heroTitle}>
            Non-Diagnostic Health Information & Navigation Platform
          </Text>
          <Text style={styles.heroBody}>
            VitaLens translates laboratory biomarkers into plain-language educational insights against printed reference ranges. It assists patients in understanding test trends and identifying licensed specialists. It does <Text style={styles.heroHighlight}>not replace clinical diagnosis, personalized treatment plans, or emergency triage</Text>.
          </Text>
        </View>

        {/* Key Safety Principles Section */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>KEY SAFETY PRINCIPLES</Text>
          <Text style={styles.sectionSubtitle}>Mandatory patient guardrails</Text>
        </View>

        <View style={styles.principlesCard}>
          {/* Principle 1: No Definitive Diagnosis */}
          <View style={styles.principleItem}>
            <View style={styles.principleIconContainer}>
              <CheckCircle2 size={18} color="#059669" />
            </View>
            <View style={styles.principleContent}>
              <Text style={styles.principleTitle}>No Definitive Diagnosis</Text>
              <Text style={styles.principleDescription}>
                The system explains biomarkers against printed reference bounds without claiming definitive disease diagnoses.
              </Text>
            </View>
          </View>

          <View style={styles.divider} />

          {/* Principle 2: No Pharmaceutical Prescriptions */}
          <View style={styles.principleItem}>
            <View style={styles.principleIconContainer}>
              <CheckCircle2 size={18} color="#059669" />
            </View>
            <View style={styles.principleContent}>
              <Text style={styles.principleTitle}>No Pharmaceutical Prescriptions</Text>
              <Text style={styles.principleDescription}>
                VitaLens never prescribes pharmaceuticals, initiates drug therapies, or suggests modifying physician-ordered medication dosages.
              </Text>
            </View>
          </View>

          <View style={styles.divider} />

          {/* Principle 3: Report-Specific Range Primacy */}
          <View style={styles.principleItem}>
            <View style={styles.principleIconContainer}>
              <CheckCircle2 size={18} color="#059669" />
            </View>
            <View style={styles.principleContent}>
              <Text style={styles.principleTitle}>Report-Specific Range Primacy</Text>
              <Text style={styles.principleDescription}>
                Reference ranges are extracted directly from your laboratory document, reflecting the specific calibrated testing methodology of that facility.
              </Text>
            </View>
          </View>

          <View style={styles.divider} />

          {/* Principle 4: Doctor-in-the-Loop Protocol */}
          <View style={styles.principleItem}>
            <View style={styles.principleIconContainer}>
              <CheckCircle2 size={18} color="#059669" />
            </View>
            <View style={styles.principleContent}>
              <Text style={styles.principleTitle}>Doctor-in-the-Loop Care</Text>
              <Text style={styles.principleDescription}>
                All AI triage outputs are structured to prepare you for informed consultations with qualified, licensed medical professionals.
              </Text>
            </View>
          </View>
        </View>

        {/* Emergency Intercept - Full-Width Danger Alert Box */}
        <View style={styles.emergencyBox}>
          <View style={styles.emergencyHeader}>
            <View style={styles.emergencyIconBadge}>
              <AlertTriangle size={18} color="#DC2626" strokeWidth={2.4} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.emergencyTitle}>EMERGENCY INTERCEPT PROTOCOL</Text>
              <Text style={styles.emergencySubtitle}>Immediate clinical escalation</Text>
            </View>
            <View style={styles.emergencyCallPill}>
              <Text style={styles.emergencyCallText}>CALL 112 / 911</Text>
            </View>
          </View>

          <Text style={styles.emergencyBody}>
            If you or someone in your care is experiencing severe chest pain, sudden numbness, difficulty breathing, acute trauma, or loss of consciousness, <Text style={styles.emergencyBold}>immediately call emergency medical services (112 / 911) or proceed to the nearest emergency hospital</Text>. VitaLens is not an acute emergency dispatch or intervention service.
          </Text>
        </View>

        {/* Regulatory Governance & Standards Card */}
        <View style={styles.governanceCard}>
          <View style={styles.governanceRow}>
            <FileText size={16} color={COLORS.textMuted} style={{ marginRight: 8 }} />
            <Text style={styles.governanceText}>
              Complies with SaMD (Software as a Medical Device) Informational Guidelines • Version {CURRENT_NOTICE_VERSION}
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* Sticky Fixed Bottom Container for Interactive Acknowledgment */}
      <View style={styles.bottomBar}>
        <View style={styles.bottomBarHelperRow}>
          <ShieldAlert size={14} color={COLORS.textMuted} style={{ marginRight: 6 }} />
          <Text style={styles.bottomBarHelperText}>
            Required patient confirmation for clinical compliance
          </Text>
        </View>

        <TouchableOpacity
          style={[
            styles.acknowledgeBtn,
            acknowledged && styles.alreadyAcknowledgedBtn,
          ]}
          onPress={handleAcknowledge}
          disabled={saving}
          activeOpacity={0.8}
        >
          {saving ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : acknowledged ? (
            <View style={styles.btnContentRow}>
              <CheckCircle2 size={18} color="#FFFFFF" style={{ marginRight: 8 }} />
              <Text style={styles.acknowledgeBtnText}>Acknowledged & Accepted</Text>
            </View>
          ) : (
            <View style={styles.btnContentRow}>
              <CheckCircle2 size={18} color="#FFFFFF" style={{ marginRight: 8 }} />
              <Text style={styles.acknowledgeBtnText}>I Understand & Accept</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>
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
    paddingBottom: 28,
  },
  ackBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginBottom: 14,
  },
  ackBannerText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#065F46',
    flex: 1,
  },
  heroCard: {
    backgroundColor: '#F0FDFA',
    borderWidth: 1.5,
    borderColor: '#CCFBF1',
    borderRadius: 22,
    padding: 18,
    marginBottom: 20,
  },
  heroTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  heroIconBox: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  complianceBadge: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  complianceBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.primaryDark,
    letterSpacing: 0.4,
  },
  heroTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: COLORS.primaryDark,
    lineHeight: 21,
    marginBottom: 8,
  },
  heroBody: {
    fontSize: 12.5,
    color: COLORS.textPrimary,
    lineHeight: 18,
  },
  heroHighlight: {
    fontWeight: '700',
    color: '#0F5C5E',
  },
  sectionHeaderRow: {
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: COLORS.textMuted,
    letterSpacing: 0.6,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  principlesCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 18,
  },
  principleItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 8,
  },
  principleIconContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
    marginRight: 12,
  },
  principleContent: {
    flex: 1,
  },
  principleTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 3,
  },
  principleDescription: {
    fontSize: 12.5,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.borderSubtle,
    marginVertical: 6,
  },
  emergencyBox: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1.5,
    borderColor: '#FECACA',
    borderRadius: 20,
    padding: 16,
    marginBottom: 18,
  },
  emergencyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  emergencyIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  emergencyTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#991B1B',
    letterSpacing: 0.3,
  },
  emergencySubtitle: {
    fontSize: 11,
    color: '#B91C1C',
    marginTop: 1,
  },
  emergencyCallPill: {
    backgroundColor: '#DC2626',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  emergencyCallText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  emergencyBody: {
    fontSize: 12,
    color: '#7F1D1D',
    lineHeight: 18,
  },
  emergencyBold: {
    fontWeight: '700',
    color: '#991B1B',
  },
  governanceCard: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    backgroundColor: 'transparent',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  governanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  governanceText: {
    fontSize: 11,
    color: COLORS.textMuted,
    lineHeight: 16,
    textAlign: 'center',
  },
  bottomBar: {
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: Platform.OS === 'ios' ? 24 : 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -3 },
        shadowOpacity: 0.06,
        shadowRadius: 6,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  bottomBarHelperRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  bottomBarHelperText: {
    fontSize: 11,
    color: COLORS.textMuted,
    fontWeight: '500',
  },
  acknowledgeBtn: {
    height: 48,
    borderRadius: 14,
    backgroundColor: COLORS.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  alreadyAcknowledgedBtn: {
    backgroundColor: '#059669',
  },
  btnContentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  acknowledgeBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
