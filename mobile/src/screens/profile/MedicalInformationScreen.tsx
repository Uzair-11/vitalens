import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  Heart,
  Droplet,
  Info,
  Phone,
  ShieldCheck,
  Save,
  CheckCircle2,
  AlertCircle,
  UserCheck,
  User,
  Users,
} from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { COLORS } from '../../constants/colors';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const BIOLOGICAL_SEX_OPTIONS = ['Male', 'Female', 'Other', 'Prefer not to say'];
const RELATION_OPTIONS = ['Spouse', 'Parent', 'Sibling', 'Child', 'Friend', 'Guardian'];

// Helper to parse emergency contact into 3 fields (name, relation, phone)
const parseEmergencyContact = (raw?: string | null) => {
  if (!raw) return { name: '', relation: 'Spouse', phone: '' };

  // Format: "Name | Relation | +91 XXXXX XXXXX"
  if (raw.includes('|')) {
    const parts = raw.split('|').map((s) => s.trim());
    const digits = (parts[2] || '').replace(/[^0-9]/g, '').slice(-10);
    const formatted = digits.length > 5 ? `${digits.slice(0, 5)} ${digits.slice(5)}` : digits;
    return {
      name: parts[0] || '',
      relation: parts[1] || 'Spouse',
      phone: formatted,
    };
  }

  // Format: "Name (Relation) - +91 XXXXX XXXXX"
  const match = raw.match(/^(.*?)\s*\((.*?)\)\s*[-:]?\s*(.*)$/);
  if (match) {
    const digits = match[3].replace(/[^0-9]/g, '').slice(-10);
    const formatted = digits.length > 5 ? `${digits.slice(0, 5)} ${digits.slice(5)}` : digits;
    return {
      name: match[1].trim(),
      relation: match[2].trim(),
      phone: formatted,
    };
  }

  // Digits only
  const phoneOnly = raw.replace(/[^0-9]/g, '');
  if (phoneOnly.length >= 10) {
    const digits = phoneOnly.slice(-10);
    const formatted = digits.length > 5 ? `${digits.slice(0, 5)} ${digits.slice(5)}` : digits;
    return {
      name: '',
      relation: 'Spouse',
      phone: formatted,
    };
  }

  return { name: raw.trim(), relation: 'Spouse', phone: '' };
};

export const MedicalInformationScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const initialBloodGroup = user?.blood_group || 'O+';
  const initialBiologicalSex = user?.biological_sex || 'Male';
  const initialContact = parseEmergencyContact(user?.emergency_contact);

  const [bloodGroup, setBloodGroup] = useState<string>(initialBloodGroup);
  const [biologicalSex, setBiologicalSex] = useState<string>(initialBiologicalSex);

  // 3 Emergency Contact Fields
  const [contactName, setContactName] = useState<string>(initialContact.name);
  const [contactPhone, setContactPhone] = useState<string>(initialContact.phone);
  const [contactRelation, setContactRelation] = useState<string>(initialContact.relation);

  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-format Indian Phone Number (10 digits formatted as XXXXX XXXXX)
  const handleContactPhoneChange = (text: string) => {
    setErrorMsg(null);
    let cleaned = text.replace(/[^0-9]/g, '');
    if (cleaned.startsWith('91') && cleaned.length > 10) {
      cleaned = cleaned.slice(2);
    } else if (cleaned.startsWith('0') && cleaned.length > 10) {
      cleaned = cleaned.slice(1);
    }
    const digits = cleaned.slice(0, 10);
    if (digits.length > 5) {
      setContactPhone(`${digits.slice(0, 5)} ${digits.slice(5)}`);
    } else {
      setContactPhone(digits);
    }
  };

  const isDirty =
    bloodGroup !== initialBloodGroup ||
    biologicalSex !== initialBiologicalSex ||
    contactName.trim() !== initialContact.name.trim() ||
    contactRelation.trim() !== initialContact.relation.trim() ||
    contactPhone.replace(/[^0-9]/g, '') !== initialContact.phone.replace(/[^0-9]/g, '');

  const handleShowSexTooltip = () => {
    Alert.alert(
      'Clinical Purpose of Biological Sex',
      'Diagnostic pathology models rely on biological sex because standard clinical reference intervals for biomarkers (such as Hemoglobin, Creatinine, Ferritin, and RBC counts) differ based on sex.\n\nYour data is strictly encrypted and governed by HIPAA & DPDP compliance standards.',
      [{ text: 'Understood' }]
    );
  };

  const handleShowBloodGroupInfo = (bg: string) => {
    let note = 'Standard blood type.';
    if (bg === 'O-') note = 'Universal RBC Donor (can donate red blood cells to any blood type).';
    if (bg === 'O+') note = 'Most common blood type in the population.';
    if (bg === 'AB+') note = 'Universal Plasma Donor & Universal Recipient.';
    Alert.alert(`Blood Group: ${bg}`, note, [{ text: 'OK' }]);
  };

  const handleSave = async () => {
    setErrorMsg(null);
    setSuccessMsg(null);

    const rawContactDigits = contactPhone.replace(/[^0-9]/g, '');
    if (rawContactDigits.length > 0 && rawContactDigits.length !== 10) {
      setErrorMsg('Please enter a valid 10-digit Indian emergency contact phone number.');
      return;
    }

    setLoading(true);

    try {
      // Build composite emergency contact string: "Name | Relation | +91 XXXXX XXXXX"
      let formattedEmergencyContact: string | undefined = undefined;
      if (contactName.trim() || rawContactDigits.length > 0) {
        const phoneFormatted = rawContactDigits.length === 10
          ? `+91 ${rawContactDigits.slice(0, 5)} ${rawContactDigits.slice(5)}`
          : rawContactDigits ? `+91 ${rawContactDigits}` : '';
        formattedEmergencyContact = `${contactName.trim()} | ${contactRelation.trim() || 'Spouse'} | ${phoneFormatted}`.trim();
      }

      const updatedUser = await authApi.updateProfile({
        blood_group: bloodGroup,
        biological_sex: biologicalSex,
        emergency_contact: formattedEmergencyContact,
      });

      updateUser(updatedUser);
      setSuccessMsg('Medical information saved successfully!');
      setTimeout(() => {
        setSuccessMsg(null);
      }, 4000);
    } catch (err: any) {
      console.error('Update medical info error:', err);
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to save medical information.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Medical Information"
        subtitle="Manage vitals, blood type & emergency contact"
        onBack={() => navigation.goBack()}
      />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          style={styles.scrollArea}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Notifications / Feedback */}
          {successMsg && (
            <View style={styles.successBanner}>
              <CheckCircle2 size={16} color={COLORS.success} style={{ marginRight: 8 }} />
              <Text style={styles.successBannerText}>{successMsg}</Text>
            </View>
          )}

          {errorMsg && (
            <View style={styles.errorBanner}>
              <AlertCircle size={16} color={COLORS.danger} style={{ marginRight: 8 }} />
              <Text style={styles.errorBannerText}>{errorMsg}</Text>
            </View>
          )}

          {/* 1. Blood Group Structured Grid Card */}
          <View style={styles.card}>
            <View style={styles.cardHeaderRow}>
              <View style={styles.cardHeaderLeft}>
                <View style={styles.headerIconBox}>
                  <Droplet size={18} color="#DC2626" />
                </View>
                <View style={{ flex: 1 }}>
                  <View style={styles.titleBadgeRow}>
                    <Text style={styles.cardTitle}>Blood Group</Text>
                    <View style={styles.activeBadgePill}>
                      <Droplet size={11} color="#DC2626" style={{ marginRight: 3 }} />
                      <Text style={styles.activeBadgeText}>{bloodGroup}</Text>
                    </View>
                  </View>
                  <Text style={styles.cardSubtitle}>Select your clinically verified blood type</Text>
                </View>
              </View>
              <TouchableOpacity
                onPress={() => handleShowBloodGroupInfo(bloodGroup)}
                style={styles.infoIconBtn}
                activeOpacity={0.7}
              >
                <Info size={18} color="#DC2626" />
              </TouchableOpacity>
            </View>

            <View style={styles.chipGrid}>
              {BLOOD_GROUPS.map((bg) => {
                const isSelected = bloodGroup === bg;
                return (
                  <TouchableOpacity
                    key={bg}
                    onPress={() => {
                      setBloodGroup(bg);
                      setErrorMsg(null);
                    }}
                    style={[styles.bloodChip, isSelected && styles.bloodChipActive]}
                    activeOpacity={0.75}
                  >
                    <Droplet
                      size={14}
                      color={isSelected ? '#ffffff' : '#DC2626'}
                      style={{ marginRight: 4 }}
                    />
                    <Text style={[styles.bloodChipText, isSelected && styles.bloodChipTextActive]}>
                      {bg}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {/* 2. Biological Sex Card with Info Tooltip */}
          <View style={styles.card}>
            <View style={styles.cardHeaderRow}>
              <View style={styles.cardHeaderLeft}>
                <View style={[styles.headerIconBox, { backgroundColor: '#EFF6FF' }]}>
                  <UserCheck size={18} color="#2563EB" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>Biological Sex</Text>
                  <Text style={styles.cardSubtitle}>Required for lab reference ranges</Text>
                </View>
              </View>
              <TouchableOpacity
                onPress={handleShowSexTooltip}
                style={[styles.infoIconBtn, { backgroundColor: '#EFF6FF' }]}
                activeOpacity={0.7}
              >
                <Info size={18} color="#2563EB" />
              </TouchableOpacity>
            </View>

            <View style={styles.sexOptionsContainer}>
              {BIOLOGICAL_SEX_OPTIONS.map((opt) => {
                const isSelected = biologicalSex === opt;
                return (
                  <TouchableOpacity
                    key={opt}
                    onPress={() => {
                      setBiologicalSex(opt);
                      setErrorMsg(null);
                    }}
                    style={[styles.sexOptionPill, isSelected && styles.sexOptionPillActive]}
                    activeOpacity={0.75}
                  >
                    <Text style={[styles.sexOptionText, isSelected && styles.sexOptionTextActive]}>
                      {opt}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {/* 3. Emergency Contact Card (3 Dedicated Fields) */}
          <View style={styles.card}>
            <View style={styles.cardHeaderRow}>
              <View style={styles.cardHeaderLeft}>
                <View style={[styles.headerIconBox, { backgroundColor: '#FEF3C7' }]}>
                  <Heart size={18} color="#D97706" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>Emergency Contact</Text>
                  <Text style={styles.cardSubtitle}>Notified in the event of critical lab findings</Text>
                </View>
              </View>
            </View>

            {/* Field 1: Contact Full Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Contact Full Name</Text>
              <View style={styles.inputWrapper}>
                <User size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  value={contactName}
                  onChangeText={(val) => {
                    setContactName(val);
                    setErrorMsg(null);
                  }}
                  placeholder="e.g. Sarah Shaikh"
                  placeholderTextColor={COLORS.textMuted}
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* Field 2: Contact Phone Number with Indian +91 prefix */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Contact Phone Number</Text>
              <View style={styles.phoneInputRow}>
                <View style={styles.prefixBox}>
                  <Text style={styles.flagEmoji}>🇮🇳</Text>
                  <Text style={styles.prefixText}>+91</Text>
                </View>
                <View style={[styles.inputWrapper, { flex: 1, marginBottom: 0 }]}>
                  <Phone size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                  <TextInput
                    value={contactPhone}
                    onChangeText={handleContactPhoneChange}
                    placeholder="98765 43210"
                    placeholderTextColor={COLORS.textMuted}
                    keyboardType="phone-pad"
                    maxLength={11}
                    style={styles.textInput}
                  />
                </View>
              </View>
            </View>

            {/* Field 3: Relationship with Quick Chips */}
            <View style={[styles.inputGroup, { marginBottom: 6 }]}>
              <Text style={styles.inputLabel}>Relationship</Text>
              <View style={styles.inputWrapper}>
                <Users size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  value={contactRelation}
                  onChangeText={(val) => {
                    setContactRelation(val);
                    setErrorMsg(null);
                  }}
                  placeholder="e.g. Spouse, Parent, Sibling"
                  placeholderTextColor={COLORS.textMuted}
                  style={styles.textInput}
                />
              </View>

              {/* Quick Select Relationship Chips */}
              <View style={styles.relationChipsRow}>
                {RELATION_OPTIONS.map((rel) => {
                  const isSelected = contactRelation.toLowerCase() === rel.toLowerCase();
                  return (
                    <TouchableOpacity
                      key={rel}
                      onPress={() => {
                        setContactRelation(rel);
                        setErrorMsg(null);
                      }}
                      style={[styles.relationChip, isSelected && styles.relationChipActive]}
                      activeOpacity={0.7}
                    >
                      <Text
                        style={[
                          styles.relationChipText,
                          isSelected && styles.relationChipTextActive,
                        ]}
                      >
                        {rel}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          </View>

          {/* 4. Privacy & Regulatory Safeguards Notice */}
          <View style={styles.privacyCard}>
            <ShieldCheck size={22} color={COLORS.primary} style={{ marginRight: 12, marginTop: 2 }} />
            <View style={{ flex: 1 }}>
              <Text style={styles.privacyTitle}>HIPAA & DPDP Protected Health Vitals</Text>
              <Text style={styles.privacyText}>
                Your medical indicators are encrypted at rest with AES-256. They are strictly utilized
                to parameterize AI biomarker range models and provide consulting physicians with clinical context.
              </Text>
            </View>
          </View>

          {/* Save Action Button */}
          <TouchableOpacity
            onPress={handleSave}
            disabled={!isDirty || loading}
            style={[styles.saveBtn, (!isDirty || loading) && styles.saveBtnDisabled]}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <>
                <Save size={18} color="#ffffff" style={{ marginRight: 8 }} />
                <Text style={styles.saveBtnText}>
                  {isDirty ? 'Save Medical Changes' : 'All Changes Saved'}
                </Text>
              </>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
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
    paddingBottom: 40,
  },
  // Banners
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
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FDE8E8',
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FBD5D5',
  },
  errorBannerText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#9B1C1C',
    flex: 1,
  },
  // Cards
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 18,
    boxShadow: '0px 2px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  cardHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  headerIconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  titleBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#1E293B',
  },
  cardSubtitle: {
    fontSize: 12,
    fontWeight: '500',
    color: '#4A4A4A',
    marginTop: 2,
  },
  activeBadgePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  activeBadgeText: {
    fontSize: 12,
    fontWeight: '900',
    color: '#DC2626',
  },
  // Blood Chip Grid
  chipGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  bloodChip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '22%',
    paddingVertical: 12,
    borderRadius: 14,
    backgroundColor: '#F8FAFC',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
  },
  bloodChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
    boxShadow: '0px 2px 6px rgba(15, 92, 94, 0.25)',
    elevation: 2,
  },
  bloodChipText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#1E293B',
  },
  bloodChipTextActive: {
    color: '#ffffff',
  },
  // Info Button
  infoIconBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 10,
  },
  // Biological Sex
  sexOptionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  sexOptionPill: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: '#F8FAFC',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
  },
  sexOptionPillActive: {
    backgroundColor: '#EFF6FF',
    borderColor: '#2563EB',
  },
  sexOptionText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#334155',
  },
  sexOptionTextActive: {
    color: '#2563EB',
    fontWeight: '800',
  },
  // 3-field Emergency Contact Inputs
  inputGroup: {
    marginBottom: 14,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 6,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 12,
    height: 48,
  },
  inputIcon: {
    marginRight: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 13,
    fontWeight: '500',
    color: '#1E293B',
  },
  phoneInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  prefixBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    height: 48,
    paddingHorizontal: 12,
    gap: 4,
  },
  flagEmoji: {
    fontSize: 16,
  },
  prefixText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
  },
  relationChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  relationChip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  relationChipActive: {
    backgroundColor: '#FEF3C7',
    borderColor: '#F59E0B',
  },
  relationChipText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#475569',
  },
  relationChipTextActive: {
    color: '#B45309',
    fontWeight: '800',
  },
  // Privacy Notice Card
  privacyCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#E6EFEF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#CCE3DE',
    marginBottom: 24,
  },
  privacyTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 4,
  },
  privacyText: {
    fontSize: 12,
    color: '#4A4A4A',
    lineHeight: 18,
  },
  // Save Button
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    height: 52,
    boxShadow: '0px 3px 6px rgba(15, 92, 94, 0.25)',
    elevation: 2,
  },
  saveBtnDisabled: {
    backgroundColor: '#94A3B8',
    opacity: 0.6,
  },
  saveBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
});
