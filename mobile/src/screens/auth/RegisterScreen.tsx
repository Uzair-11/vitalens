import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Image,
  ActivityIndicator,
  Modal,
} from 'react-native';
import {
  User,
  Mail,
  Lock,
  Phone,
  Calendar,
  Eye,
  EyeOff,
  Check,
  ArrowRight,
  Shield,
  AlertCircle,
} from 'lucide-react-native';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { COLORS } from '../../constants/colors';
import { User as UserProfile } from '../../types';

export const RegisterScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  // Form fields
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [dob, setDob] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // UI state
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [agreedToPrivacy, setAgreedToPrivacy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  const setAuth = useAuthStore((state) => state.setAuth);

  // Auto-format Indian Phone Number (10 digits formatted as XXXXX XXXXX)
  const handlePhoneChange = (text: string) => {
    setErrorText(null);
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
    setErrorText(null);
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

  // Field validation helpers
  const isValidEmail = (val: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim());
  };

  const isValidDob = (val: string) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(val)) return false;
    const [year, month, day] = val.split('-').map(Number);
    const now = new Date();
    const currentYear = now.getFullYear();
    if (year < 1910 || year > currentYear) return false;
    if (month < 1 || month > 12) return false;
    if (day < 1 || day > 31) return false;

    const parsed = new Date(year, month - 1, day);
    return (
      parsed.getFullYear() === year &&
      parsed.getMonth() === month - 1 &&
      parsed.getDate() === day &&
      parsed <= now
    );
  };

  const handleRegister = async () => {
    setErrorText(null);

    // 1. Validation checks
    if (!fullName.trim()) {
      setErrorText('Please enter your full name.');
      return;
    }
    if (fullName.trim().length < 2) {
      setErrorText('Full name must be at least 2 characters.');
      return;
    }

    if (!email.trim() || !isValidEmail(email)) {
      setErrorText('Please enter a valid email address.');
      return;
    }

    const rawPhoneDigits = phone.replace(/[^0-9]/g, '');
    if (!rawPhoneDigits) {
      setErrorText('Please enter your 10-digit mobile number.');
      return;
    }
    if (rawPhoneDigits.length !== 10) {
      setErrorText('Please enter a valid 10-digit Indian mobile number.');
      return;
    }

    if (!dob.trim()) {
      setErrorText('Please enter your date of birth (YYYY-MM-DD).');
      return;
    }
    if (!isValidDob(dob.trim())) {
      setErrorText('Invalid date of birth. Please use format YYYY-MM-DD (e.g. 1996-05-14).');
      return;
    }

    if (!password) {
      setErrorText('Please create a password.');
      return;
    }
    if (password.length < 8) {
      setErrorText('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorText('Passwords do not match. Please re-enter.');
      return;
    }

    if (!agreedToPrivacy) {
      setErrorText('You must agree to the Privacy Policy & Terms of Service to register.');
      return;
    }

    setLoading(true);

    try {
      const formattedPhone = `+91 ${rawPhoneDigits.slice(0, 5)} ${rawPhoneDigits.slice(5)}`;
      const data = await authApi.register({
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim(),
        phone: formattedPhone,
        date_of_birth: dob.trim(),
      });

      let profile: UserProfile;
      try {
        profile = await authApi.getProfile(data.access_token);
      } catch (profErr) {
        profile = {
          id: data.user_id,
          email: data.email,
          full_name: data.full_name || fullName.trim(),
          phone: formattedPhone,
          date_of_birth: dob.trim(),
          created_at: new Date().toISOString(),
        };
      }

      await setAuth(data.access_token, profile, data.refresh_token);
    } catch (err: any) {
      console.error('Registration error:', err);
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        (err.message === 'Network Error'
          ? 'Cannot connect to backend server. Make sure the FastAPI backend is running.'
          : 'Registration failed. Please check your details and try again.');
      setErrorText(msg);
      if (Platform.OS !== 'web') {
        Alert.alert('Registration Failed', msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const passwordsMatch = password.length > 0 && confirmPassword.length > 0 && password === confirmPassword;
  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword;

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Logo Header (Icon only, no wordmark or tagline) */}
          <View style={styles.headerBox}>
            <Image
              source={require('../../../assets/images/vitalens-icon.png')}
              style={styles.brandLogo}
              resizeMode="contain"
            />
          </View>

          {/* Form Card */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Create Account</Text>
              <Text style={styles.cardSubtitle}>
                Register to securely analyze lab reports and access specialist care
              </Text>
            </View>

            {/* Error Banner */}
            {errorText && (
              <View style={styles.errorBanner}>
                <AlertCircle size={16} color={COLORS.danger} style={{ marginRight: 8, marginTop: 2 }} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.errorBannerText}>{errorText}</Text>
                  {errorText.toLowerCase().includes('already exists') && (
                    <TouchableOpacity
                      onPress={() => navigation.navigate('Login')}
                      style={{ marginTop: 6 }}
                    >
                      <Text style={{ fontSize: 12.5, fontWeight: '800', color: COLORS.primaryDark }}>
                        👉 Account already exists! Tap to Sign In
                      </Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            )}

            {/* 1. Full Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                Full Name <Text style={styles.requiredAsterisk}>*</Text>
              </Text>
              <View style={styles.inputWrapper}>
                <User size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  value={fullName}
                  onChangeText={(val) => {
                    setFullName(val);
                    setErrorText(null);
                  }}
                  placeholder="e.g. John Doe"
                  placeholderTextColor={COLORS.textMuted}
                  autoCapitalize="words"
                  autoCorrect={false}
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* 2. Email Address */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                Email Address <Text style={styles.requiredAsterisk}>*</Text>
              </Text>
              <View style={styles.inputWrapper}>
                <Mail size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  value={email}
                  onChangeText={(val) => {
                    setEmail(val);
                    setErrorText(null);
                  }}
                  placeholder="name@example.com"
                  placeholderTextColor={COLORS.textMuted}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  autoCorrect={false}
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* 3. Phone Number (India +91) */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                Phone Number <Text style={styles.requiredAsterisk}>*</Text>
              </Text>
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

            {/* 4. Date of Birth (DOB) */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>
                  Date of Birth <Text style={styles.requiredAsterisk}>*</Text>
                </Text>
                <Text style={styles.inputHint}>YYYY-MM-DD</Text>
              </View>
              <View style={styles.inputWrapper}>
                <Calendar size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
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
            </View>

            {/* 5. Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                Password <Text style={styles.requiredAsterisk}>*</Text>
              </Text>
              <View style={styles.inputWrapper}>
                <Lock size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  value={password}
                  onChangeText={(val) => {
                    setPassword(val);
                    setErrorText(null);
                  }}
                  placeholder="Min 8 characters"
                  placeholderTextColor={COLORS.textMuted}
                  secureTextEntry={!showPassword}
                  style={styles.textInput}
                />
                <TouchableOpacity
                  onPress={() => setShowPassword(!showPassword)}
                  style={styles.eyeBtn}
                  activeOpacity={0.7}
                >
                  {showPassword ? (
                    <EyeOff size={18} color={COLORS.textSecondary} />
                  ) : (
                    <Eye size={18} color={COLORS.textSecondary} />
                  )}
                </TouchableOpacity>
              </View>
            </View>

            {/* 6. Confirm Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>
                Confirm Password <Text style={styles.requiredAsterisk}>*</Text>
              </Text>
              <View
                style={[
                  styles.inputWrapper,
                  passwordsMatch && styles.inputWrapperSuccess,
                  passwordsMismatch && styles.inputWrapperError,
                ]}
              >
                <Lock
                  size={18}
                  color={
                    passwordsMatch
                      ? COLORS.success
                      : passwordsMismatch
                      ? COLORS.danger
                      : COLORS.textSecondary
                  }
                  style={styles.inputIcon}
                />
                <TextInput
                  value={confirmPassword}
                  onChangeText={(val) => {
                    setConfirmPassword(val);
                    setErrorText(null);
                  }}
                  placeholder="Re-enter password"
                  placeholderTextColor={COLORS.textMuted}
                  secureTextEntry={!showConfirmPassword}
                  style={styles.textInput}
                />
                <TouchableOpacity
                  onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                  style={styles.eyeBtn}
                  activeOpacity={0.7}
                >
                  {showConfirmPassword ? (
                    <EyeOff size={18} color={COLORS.textSecondary} />
                  ) : (
                    <Eye size={18} color={COLORS.textSecondary} />
                  )}
                </TouchableOpacity>
              </View>
              {passwordsMatch && (
                <View style={styles.matchFeedbackRow}>
                  <Check size={14} color={COLORS.success} />
                  <Text style={styles.matchFeedbackText}>Passwords match</Text>
                </View>
              )}
              {passwordsMismatch && (
                <View style={styles.matchFeedbackRow}>
                  <AlertCircle size={14} color={COLORS.danger} />
                  <Text style={[styles.matchFeedbackText, { color: COLORS.danger }]}>
                    Passwords do not match
                  </Text>
                </View>
              )}
            </View>

            {/* Privacy Policy & Terms Checkbox */}
            <TouchableOpacity
              onPress={() => {
                setAgreedToPrivacy(!agreedToPrivacy);
                setErrorText(null);
              }}
              style={styles.privacyRow}
              activeOpacity={0.8}
            >
              <View
                style={[
                  styles.checkbox,
                  agreedToPrivacy && styles.checkboxActive,
                ]}
              >
                {agreedToPrivacy && <Check size={14} color="#ffffff" strokeWidth={3} />}
              </View>
              <View style={styles.privacyTextContainer}>
                <Text style={styles.privacyText}>
                  I agree to the{' '}
                  <Text
                    style={styles.privacyLink}
                    onPress={() => setShowPolicyModal(true)}
                  >
                    Privacy Policy
                  </Text>{' '}
                  and{' '}
                  <Text
                    style={styles.privacyLink}
                    onPress={() => setShowPolicyModal(true)}
                  >
                    Terms of Service
                  </Text>
                  .
                </Text>
              </View>
            </TouchableOpacity>

            {/* Register Button */}
            <TouchableOpacity
              onPress={handleRegister}
              disabled={loading}
              activeOpacity={0.85}
              style={[styles.primaryBtn, loading && styles.btnDisabled]}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#ffffff" />
              ) : (
                <>
                  <Text style={styles.primaryBtnText}>Create Account</Text>
                  <ArrowRight size={18} color="#ffffff" style={{ marginLeft: 8 }} />
                </>
              )}
            </TouchableOpacity>
          </View>

          {/* Link to Login */}
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>Already have an account? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Login')}>
              <Text style={styles.loginLinkText}>Sign In</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* Privacy Policy & Terms Modal */}
      <Modal
        visible={showPolicyModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowPolicyModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Shield size={24} color={COLORS.primary} style={{ marginRight: 8 }} />
              <Text style={styles.modalTitle}>Privacy & Clinical Terms</Text>
            </View>

            <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={true}>
              <Text style={styles.modalSectionTitle}>1. Medical Information Notice</Text>
              <Text style={styles.modalSectionText}>
                VitaLens utilizes Artificial Intelligence to extract biomarkers and provide plain-language
                explanations of diagnostic laboratory reports. VitaLens does not provide formal medical
                diagnoses. Insights generated are intended for educational and triage guidance only. Always
                consult a licensed physician before making healthcare decisions.
              </Text>

              <Text style={styles.modalSectionTitle}>2. Data Encryption & HIPAA/DPDP Privacy</Text>
              <Text style={styles.modalSectionText}>
                Your medical reports, biomarker records, and demographic details are encrypted both in transit
                (TLS 1.3) and at rest (AES-256). Your health records are never shared with third parties or
                advertisers without your explicit consent.
              </Text>

              <Text style={styles.modalSectionTitle}>3. Emergency Guidance</Text>
              <Text style={styles.modalSectionText}>
                VitaLens is not designed for acute emergencies. If you are experiencing chest pain, severe
                shortness of breath, acute neurological symptoms, or any other emergency, immediately call
                your local emergency number (e.g. 911 / 112) or visit the nearest emergency room.
              </Text>
            </ScrollView>

            <TouchableOpacity
              onPress={() => {
                setAgreedToPrivacy(true);
                setShowPolicyModal(false);
              }}
              style={styles.modalAcceptBtn}
              activeOpacity={0.85}
            >
              <Text style={styles.modalAcceptBtnText}>I Understand & Agree</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 24,
    maxWidth: 480,
    alignSelf: 'center',
    width: '100%',
  },
  headerBox: {
    alignItems: 'center',
    marginBottom: 20,
  },
  brandLogo: {
    width: 100,
    height: 100,
    marginBottom: 6,
  },
  brandName: {
    fontSize: 26,
    fontWeight: '900',
    color: COLORS.primaryDark,
    letterSpacing: -0.5,
    marginBottom: 2,
  },
  brandSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    letterSpacing: 0.1,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 22,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 4px 12px rgba(38, 51, 52, 0.05)',
    elevation: 3,
  },
  cardHeader: {
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.dangerLight,
    borderWidth: 1,
    borderColor: COLORS.danger,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 16,
  },
  errorBannerText: {
    fontSize: 12,
    color: COLORS.danger,
    fontWeight: '600',
    flex: 1,
  },
  inputGroup: {
    marginBottom: 14,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 5,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 5,
  },
  requiredAsterisk: {
    color: COLORS.danger,
  },
  inputHint: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.textMuted,
  },
  toggleText: {
    fontSize: 12,
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
    paddingHorizontal: 12,
    height: 48,
  },
  inputWrapperSuccess: {
    borderColor: COLORS.success,
  },
  inputWrapperError: {
    borderColor: COLORS.danger,
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
    color: COLORS.textPrimary,
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
    color: COLORS.textPrimary,
    height: '100%',
  },
  eyeBtn: {
    padding: 6,
  },
  matchFeedbackRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    marginLeft: 4,
    gap: 4,
  },
  matchFeedbackText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.success,
  },
  privacyRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 6,
    marginBottom: 18,
    paddingHorizontal: 2,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.8,
    borderColor: COLORS.border,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  checkboxActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  privacyTextContainer: {
    flex: 1,
  },
  privacyText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
  privacyLink: {
    color: COLORS.primary,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    height: 52,
    boxShadow: '0px 3px 6px rgba(15, 92, 94, 0.25)',
    elevation: 2,
  },
  btnDisabled: {
    opacity: 0.6,
  },
  primaryBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 8,
  },
  footerText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  loginLinkText: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.primary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 22,
    width: '100%',
    maxWidth: 480,
    maxHeight: '80%',
    boxShadow: '0px 8px 24px rgba(0, 0, 0, 0.2)',
    elevation: 8,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  modalBody: {
    marginBottom: 18,
  },
  modalSectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginTop: 10,
    marginBottom: 4,
  },
  modalSectionText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 19,
    marginBottom: 10,
  },
  modalAcceptBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
  },
  modalAcceptBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
});
