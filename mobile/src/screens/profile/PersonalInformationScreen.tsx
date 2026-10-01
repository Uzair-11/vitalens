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
  Image,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  User,
  Mail,
  Calendar,
  Camera,
  CheckCircle2,
  Lock,
  Save,
  Check,
  AlertCircle,
} from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import { Header } from '../../components/common/Header';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { COLORS } from '../../constants/colors';
import { getMediaUrl } from '../../constants/config';

export const PersonalInformationScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  // Form states initialized from user session
  const initialName = user?.full_name || '';
  const initialEmail = user?.email || '';
  const initialAvatar = getMediaUrl(user?.avatar_url) || null;
  
  // Format initial phone (strip +91 prefix for input display)
  const formatInitialPhone = (p?: string) => {
    if (!p) return '';
    const digits = p.replace(/[^0-9]/g, '');
    const local10 = digits.startsWith('91') && digits.length > 10 ? digits.slice(2) : digits;
    if (local10.length > 5) {
      return `${local10.slice(0, 5)} ${local10.slice(5, 10)}`;
    }
    return local10;
  };

  const initialPhone = formatInitialPhone(user?.phone);
  const initialDob = user?.date_of_birth || '';

  const [fullName, setFullName] = useState(initialName);
  const [phone, setPhone] = useState(initialPhone);
  const [dob, setDob] = useState(initialDob);
  const [profileImageUri, setProfileImageUri] = useState<string | null>(initialAvatar);

  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-format Indian Phone Number (10 digits formatted as XXXXX XXXXX)
  const handlePhoneChange = (text: string) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    let cleaned = text.replace(/[^0-9]/g, '');
    if (cleaned.startsWith('91') && cleaned.length > 10) {
      cleaned = cleaned.slice(2);
    } else if (cleaned.startsWith('0') && cleaned.length > 10) {
      cleaned = cleaned.slice(1);
    }
    const digits = cleaned.slice(0, 10);
    if (digits.length > 5) {
      setPhone(`${digits.slice(0, 5)} ${digits.slice(5)}`);
    } else {
      setPhone(digits);
    }
  };

  // Auto-format Date of Birth to YYYY-MM-DD
  const handleDobChange = (text: string) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    if (text.length < dob.length) {
      setDob(text);
      return;
    }
    const digitsOnly = text.replace(/[^0-9]/g, '');
    if (digitsOnly.length <= 4) {
      setDob(digitsOnly);
    } else if (digitsOnly.length <= 6) {
      setDob(`${digitsOnly.slice(0, 4)}-${digitsOnly.slice(4)}`);
    } else {
      setDob(`${digitsOnly.slice(0, 4)}-${digitsOnly.slice(4, 6)}-${digitsOnly.slice(6, 8)}`);
    }
  };

  // Pick profile photo from gallery
  const handlePickPhoto = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(
          'Permission Needed',
          'Gallery access permission is required to update your profile photo.'
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setProfileImageUri(result.assets[0].uri);
        setSuccessMsg('Photo selected! Tap "Save Changes" to upload & apply.');
      }
    } catch (e) {
      Alert.alert('Photo Picker Error', 'Could not open image library.');
    }
  };

  // Calculate age if valid DOB
  const calculateAge = (dobString: string) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dobString)) return null;
    const [y, m, d] = dobString.split('-').map(Number);
    const birthDate = new Date(y, m - 1, d);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const mDiff = today.getMonth() - birthDate.getMonth();
    if (mDiff < 0 || (mDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age >= 0 && age < 120 ? age : null;
  };

  const age = calculateAge(dob);

  // Check if form has modified changes
  const isDirty =
    fullName.trim() !== initialName ||
    phone.trim() !== initialPhone ||
    dob.trim() !== initialDob ||
    profileImageUri !== initialAvatar;

  const handleSave = async () => {
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!fullName.trim() || fullName.trim().length < 2) {
      setErrorMsg('Please enter a valid full name (minimum 2 characters).');
      return;
    }

    const rawPhoneDigits = phone.replace(/[^0-9]/g, '');
    if (rawPhoneDigits.length !== 10) {
      setErrorMsg('Please enter a valid 10-digit Indian mobile number.');
      return;
    }

    if (dob.trim() && !/^\d{4}-\d{2}-\d{2}$/.test(dob.trim())) {
      setErrorMsg('Please enter a valid date of birth in YYYY-MM-DD format.');
      return;
    }

    setLoading(true);

    try {
      let currentUserData = user;

      // 1. Upload avatar if selected and changed from initial
      if (profileImageUri && profileImageUri !== initialAvatar) {
        currentUserData = await authApi.uploadAvatar(profileImageUri);
      }

      // 2. Update profile text attributes
      const formattedPhone = `+91 ${rawPhoneDigits.slice(0, 5)} ${rawPhoneDigits.slice(5)}`;
      const updatedUser = await authApi.updateProfile({
        full_name: fullName.trim(),
        phone: formattedPhone,
        date_of_birth: dob.trim() || undefined,
      });

      const mergedUser = { ...(currentUserData || {}), ...updatedUser };
      updateUser(mergedUser);
      setSuccessMsg('Personal information and profile picture updated successfully!');
      setTimeout(() => {
        setSuccessMsg(null);
      }, 4000);
    } catch (err: any) {
      console.error('Update profile error:', err);
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to update personal information.');
    } finally {
      setLoading(false);
    }
  };

  const initialLetter = (fullName.trim() || 'U').charAt(0).toUpperCase();

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Personal Information"
        subtitle="Manage your identity, contact & photo"
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
          {/* Avatar Integration with Camera Overlay */}
          <View style={styles.avatarSection}>
            <View style={styles.avatarWrapper}>
              {profileImageUri ? (
                <Image source={{ uri: profileImageUri }} style={styles.avatarImage} />
              ) : (
                <View style={styles.avatarCircle}>
                  <Text style={styles.avatarInitial}>{initialLetter}</Text>
                </View>
              )}
              <TouchableOpacity
                onPress={handlePickPhoto}
                style={styles.cameraBtn}
                activeOpacity={0.8}
              >
                <Camera size={16} color="#ffffff" strokeWidth={2.5} />
              </TouchableOpacity>
            </View>
            <TouchableOpacity onPress={handlePickPhoto} activeOpacity={0.7}>
              <Text style={styles.changePhotoText}>Change Profile Photo</Text>
            </TouchableOpacity>
          </View>

          {/* Feedback Banners */}
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

          {/* Form Card */}
          <View style={styles.card}>
            {/* 1. Full Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Full Name</Text>
              <View style={styles.inputWrapper}>
                <User size={18} color={COLORS.primary} style={styles.inputIcon} />
                <TextInput
                  value={fullName}
                  onChangeText={(val) => {
                    setFullName(val);
                    setErrorMsg(null);
                  }}
                  placeholder="e.g. Uzair Shaikh"
                  placeholderTextColor={COLORS.textMuted}
                  autoCapitalize="words"
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* 2. Email Address (Account ID - Read-Only) */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>Email Address</Text>
                <View style={styles.verifiedBadge}>
                  <Lock size={11} color="#64748B" style={{ marginRight: 3 }} />
                  <Text style={styles.verifiedBadgeText}>Primary ID</Text>
                </View>
              </View>
              <View style={[styles.inputWrapper, styles.inputWrapperDisabled]}>
                <Mail size={18} color="#64748B" style={styles.inputIcon} />
                <TextInput
                  value={initialEmail}
                  editable={false}
                  placeholderTextColor={COLORS.textMuted}
                  style={[styles.textInput, styles.textInputDisabled]}
                />
              </View>
              <Text style={styles.fieldHint}>
                Your email is your authenticated VitaLens identifier and cannot be edited.
              </Text>
            </View>

            {/* 3. Phone Number with Verified Badge */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>Phone Number</Text>
                <View style={styles.phoneVerifiedPill}>
                  <Check size={11} color="#166534" strokeWidth={3} style={{ marginRight: 3 }} />
                  <Text style={styles.phoneVerifiedText}>Verified</Text>
                </View>
              </View>
              <View style={styles.inputWrapper}>
                <View style={styles.countryCodeBadge}>
                  <Text style={styles.flagEmoji}>🇮🇳</Text>
                  <Text style={styles.countryCodeText}>+91</Text>
                  <View style={styles.countryCodeDivider} />
                </View>
                <TextInput
                  value={phone}
                  onChangeText={handlePhoneChange}
                  placeholder="98765 43210"
                  placeholderTextColor={COLORS.textMuted}
                  keyboardType="phone-pad"
                  maxLength={11}
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* 4. Date of Birth */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>Date of Birth</Text>
                {age !== null && (
                  <Text style={styles.ageBadgeText}>Age: {age} yrs</Text>
                )}
              </View>
              <View style={styles.inputWrapper}>
                <Calendar size={18} color={COLORS.primary} style={styles.inputIcon} />
                <TextInput
                  value={dob}
                  onChangeText={handleDobChange}
                  placeholder="YYYY-MM-DD (e.g. 1996-05-14)"
                  placeholderTextColor={COLORS.textMuted}
                  keyboardType="numeric"
                  maxLength={10}
                  style={styles.textInput}
                />
              </View>
              <Text style={styles.fieldHint}>
                Used to calculate accurate age-adjusted clinical biomarker ranges.
              </Text>
            </View>
          </View>

          {/* Action Button: Save Changes */}
          <TouchableOpacity
            onPress={handleSave}
            disabled={!isDirty || loading}
            style={[styles.saveBtn, (!isDirty || loading) && styles.saveBtnDisabled]}
            activeOpacity={0.85}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <>
                <Save size={18} color="#ffffff" strokeWidth={2.2} style={{ marginRight: 8 }} />
                <Text style={styles.saveBtnText}>Save Changes</Text>
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
    paddingTop: 20,
    paddingBottom: 36,
  },
  // Avatar Section
  avatarSection: {
    alignItems: 'center',
    marginBottom: 20,
  },
  avatarWrapper: {
    position: 'relative',
    marginBottom: 8,
  },
  avatarCircle: {
    width: 84,
    height: 84,
    borderRadius: 28,
    backgroundColor: '#E0ECE7',
    borderWidth: 2,
    borderColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarImage: {
    width: 84,
    height: 84,
    borderRadius: 28,
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  avatarInitial: {
    fontSize: 34,
    fontWeight: '900',
    color: COLORS.primaryDark,
  },
  cameraBtn: {
    position: 'absolute',
    bottom: -4,
    right: -4,
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: COLORS.primary,
    borderWidth: 2,
    borderColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 3,
    boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.15)',
  },
  changePhotoText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primary,
    marginTop: 2,
  },
  // Banners
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.successLight,
    borderWidth: 1,
    borderColor: '#86EFAC',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 16,
  },
  successBannerText: {
    fontSize: 13,
    color: COLORS.success,
    fontWeight: '600',
    flex: 1,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.dangerLight,
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 16,
  },
  errorBannerText: {
    fontSize: 13,
    color: COLORS.danger,
    fontWeight: '600',
    flex: 1,
  },
  // Form Card
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 20,
    boxShadow: '0px 2px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
  },
  inputGroup: {
    marginBottom: 16,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 6,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
  },
  verifiedBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
  },
  phoneVerifiedPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 2.5,
    borderRadius: 6,
  },
  phoneVerifiedText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#166534',
    letterSpacing: 0.2,
  },
  ageBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.primary,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    height: 50,
  },
  inputWrapperDisabled: {
    backgroundColor: '#F8FAFC',
    borderColor: '#E2E8F0',
  },
  countryCodeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: 8,
    marginRight: 6,
  },
  flagEmoji: {
    fontSize: 16,
    marginRight: 5,
  },
  countryCodeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
    marginRight: 8,
  },
  countryCodeDivider: {
    width: 1,
    height: 20,
    backgroundColor: COLORS.border,
  },
  inputIcon: {
    marginRight: 10,
  },
  textInput: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    color: '#1E293B',
    height: '100%',
  },
  textInputDisabled: {
    color: '#64748B',
  },
  fieldHint: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 5,
    marginLeft: 2,
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
