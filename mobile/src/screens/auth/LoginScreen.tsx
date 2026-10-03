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
  Modal,
  ActivityIndicator,
} from 'react-native';
import {
  Lock,
  Mail,
  ArrowRight,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  X,
  KeyRound,
} from 'lucide-react-native';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { COLORS } from '../../constants/colors';
import { User } from '../../types';

export const LoginScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState('');
  const [successText, setSuccessText] = useState('');

  // Forgot / Reset Password Modal State (via Email OTP)
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotStep, setForgotStep] = useState<'EMAIL' | 'OTP_RESET'>('EMAIL');
  const [resetEmail, setResetEmail] = useState('');
  const [resetOtp, setResetOtp] = useState('');
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetInfoMsg, setResetInfoMsg] = useState('');

  const setAuth = useAuthStore((state) => state.setAuth);

  const handleLogin = async (overrideEmail?: string, overridePassword?: string) => {
    const loginEmail = (overrideEmail || email).trim().toLowerCase();
    const loginPass = overridePassword || password;

    if (!loginEmail || !loginPass.trim()) {
      setErrorText('Please provide both email address and password.');
      return;
    }

    setErrorText('');
    setSuccessText('');
    setLoading(true);

    try {
      const data = await authApi.login(loginEmail, loginPass);
      let profile: User;
      try {
        profile = await authApi.getProfile(data.access_token);
      } catch (profErr) {
        profile = {
          id: data.user_id,
          email: data.email,
          full_name: data.full_name,
          role: data.role,
          created_at: new Date().toISOString(),
        };
      }
      if (!profile.role && data.role) {
        profile.role = data.role;
      }

      await setAuth(data.access_token, profile, data.refresh_token);
    } catch (err: any) {
      console.error('Login error:', err);
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        (err.message === 'Network Error'
          ? 'Cannot connect to backend server. Make sure the FastAPI backend is running.'
          : 'Invalid email or password credentials.');
      setErrorText(msg);
      if (Platform.OS !== 'web') {
        Alert.alert('Sign In Failed', msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRequestResetOtp = async () => {
    const targetEmail = resetEmail.trim().toLowerCase();
    if (!targetEmail) {
      setResetError('Please enter your registered email address.');
      return;
    }

    setResetError('');
    setResetInfoMsg('');
    setResetLoading(true);

    try {
      const res = await authApi.forgotPasswordRequestOtp(targetEmail);
      setForgotStep('OTP_RESET');
      setResetInfoMsg(res.message || `A 6-digit OTP code has been sent to ${targetEmail}.`);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to dispatch reset code. Please check your email.';
      setResetError(msg);
    } finally {
      setResetLoading(false);
    }
  };

  const handleResetPassword = async () => {
    const targetEmail = resetEmail.trim().toLowerCase();
    if (!targetEmail) {
      setResetError('Please enter your email address.');
      return;
    }
    const cleanOtp = resetOtp.trim();
    if (!cleanOtp || cleanOtp.length !== 6) {
      setResetError('Please enter the 6-digit OTP code sent to your email.');
      return;
    }
    if (resetNewPassword.length < 6) {
      setResetError('New password must be at least 6 characters long.');
      return;
    }
    if (resetNewPassword !== resetConfirmPassword) {
      setResetError('Passwords do not match.');
      return;
    }

    setResetError('');
    setResetLoading(true);

    try {
      await authApi.forgotPasswordReset(targetEmail, cleanOtp, resetNewPassword);
      setShowForgotModal(false);
      setForgotStep('EMAIL');
      setResetOtp('');
      setEmail(targetEmail);
      setPassword(resetNewPassword);
      setSuccessText('Password updated successfully via OTP! Signing you in...');
      // Auto-login with the new password
      await handleLogin(targetEmail, resetNewPassword);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to reset password. Please check the code.';
      setResetError(msg);
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {/* Brand Header */}
          <View style={styles.headerBox}>
            <Image
              source={require('../../../assets/images/vitalens-icon.png')}
              style={styles.brandLogo}
              resizeMode="contain"
            />
          </View>

          {/* Form Card */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Welcome Back</Text>
            <Text style={styles.cardSubtitle}>Sign in to access your reports & specialist care</Text>

            {/* Error Banner */}
            {errorText ? (
              <View style={styles.errorBanner}>
                <AlertCircle size={16} color={COLORS.danger} style={{ marginRight: 8, marginTop: 2 }} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.errorBannerText}>{errorText}</Text>
                  {errorText.toLowerCase().includes('password') && (
                    <TouchableOpacity
                      onPress={() => {
                        setResetEmail(email.trim());
                        setResetError('');
                        setShowForgotModal(true);
                      }}
                      style={{ marginTop: 4 }}
                    >
                      <Text style={styles.resetPromptLink}>Forgot password? Tap here to reset it.</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            ) : null}

            {/* Success Banner */}
            {successText ? (
              <View style={styles.successBanner}>
                <CheckCircle2 size={16} color={COLORS.success} style={{ marginRight: 8, marginTop: 2 }} />
                <Text style={styles.successBannerText}>{successText}</Text>
              </View>
            ) : null}

            {/* Email Field */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Email Address</Text>
              <View style={styles.inputWrapper}>
                <Mail size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  value={email}
                  onChangeText={(val) => {
                    setEmail(val);
                    if (errorText) setErrorText('');
                  }}
                  placeholder="name@example.com"
                  placeholderTextColor={COLORS.textMuted}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* Password Field */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>Password</Text>
                <TouchableOpacity
                  onPress={() => {
                    setResetEmail(email.trim());
                    setResetError('');
                    setShowForgotModal(true);
                  }}
                >
                  <Text style={styles.forgotText}>Forgot Password?</Text>
                </TouchableOpacity>
              </View>

              <View style={styles.inputWrapper}>
                <Lock size={18} color={COLORS.textSecondary} style={styles.inputIcon} />
                <TextInput
                  value={password}
                  onChangeText={(val) => {
                    setPassword(val);
                    if (errorText) setErrorText('');
                  }}
                  placeholder="••••••••"
                  placeholderTextColor={COLORS.textMuted}
                  secureTextEntry={!showPassword}
                  style={styles.textInput}
                />
                <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeBtn}>
                  {showPassword ? (
                    <EyeOff size={18} color={COLORS.textSecondary} />
                  ) : (
                    <Eye size={18} color={COLORS.textSecondary} />
                  )}
                </TouchableOpacity>
              </View>
            </View>

            {/* Sign In Button */}
            <TouchableOpacity
              onPress={() => handleLogin()}
              disabled={loading}
              activeOpacity={0.85}
              style={[styles.primaryBtn, loading && styles.btnDisabled]}
            >
              {loading ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <>
                  <Text style={styles.primaryBtnText}>Sign In</Text>
                  <ArrowRight size={18} color="#ffffff" style={{ marginLeft: 8 }} />
                </>
              )}
            </TouchableOpacity>
          </View>

          {/* Switch to Register */}
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>Don't have an account? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Register')}>
              <Text style={styles.signupText}>Create Account</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* Reset Password Modal */}
      <Modal
        visible={showForgotModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowForgotModal(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.modalOverlay}
        >
          <View style={styles.modalCard}>
            <View style={styles.modalHeaderRow}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <View style={styles.modalHeaderIcon}>
                  <KeyRound size={18} color={COLORS.primary} />
                </View>
                <Text style={styles.modalTitle}>Reset Password</Text>
              </View>
              <TouchableOpacity onPress={() => setShowForgotModal(false)} style={styles.closeBtn}>
                <X size={20} color="#64748B" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalSubtitle}>
              {forgotStep === 'EMAIL'
                ? "Enter your registered email address to receive a secure 6-digit OTP code."
                : `Enter the 6-digit code sent to ${resetEmail} and choose a new password.`}
            </Text>

            {resetInfoMsg ? (
              <View style={[styles.modalErrorBanner, { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' }]}>
                <CheckCircle2 size={15} color="#059669" style={{ marginRight: 6 }} />
                <Text style={[styles.modalErrorText, { color: '#047857' }]}>{resetInfoMsg}</Text>
              </View>
            ) : null}

            {resetError ? (
              <View style={styles.modalErrorBanner}>
                <AlertCircle size={15} color={COLORS.danger} style={{ marginRight: 6 }} />
                <Text style={styles.modalErrorText}>{resetError}</Text>
              </View>
            ) : null}

            {forgotStep === 'EMAIL' ? (
              <>
                <View style={styles.modalInputGroup}>
                  <Text style={styles.inputLabel}>Account Email</Text>
                  <TextInput
                    value={resetEmail}
                    onChangeText={(val) => {
                      setResetEmail(val);
                      setResetError('');
                    }}
                    placeholder="name@example.com"
                    placeholderTextColor={COLORS.textMuted}
                    autoCapitalize="none"
                    keyboardType="email-address"
                    style={styles.modalTextInput}
                  />
                </View>

                <TouchableOpacity
                  onPress={handleRequestResetOtp}
                  disabled={resetLoading}
                  activeOpacity={0.85}
                  style={[styles.primaryBtn, { marginTop: 12 }, resetLoading && styles.btnDisabled]}
                >
                  {resetLoading ? (
                    <ActivityIndicator color="#ffffff" size="small" />
                  ) : (
                    <Text style={styles.primaryBtnText}>Send OTP Reset Code</Text>
                  )}
                </TouchableOpacity>
              </>
            ) : (
              <>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <Text style={{ fontSize: 12, color: COLORS.textSecondary }}>
                    Target: <Text style={{ fontWeight: '700', color: COLORS.textPrimary }}>{resetEmail}</Text>
                  </Text>
                  <TouchableOpacity onPress={() => { setForgotStep('EMAIL'); setResetError(''); }}>
                    <Text style={{ fontSize: 12, fontWeight: '700', color: COLORS.primary }}>Change</Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.modalInputGroup}>
                  <Text style={styles.inputLabel}>6-Digit OTP Code *</Text>
                  <TextInput
                    value={resetOtp}
                    onChangeText={(val) => {
                      setResetOtp(val.replace(/[^0-9]/g, ''));
                      setResetError('');
                    }}
                    placeholder="Enter 6-digit code"
                    placeholderTextColor={COLORS.textMuted}
                    keyboardType="number-pad"
                    maxLength={6}
                    style={[styles.modalTextInput, { letterSpacing: 4, fontWeight: '700', fontSize: 16 }]}
                  />
                </View>

                <View style={styles.modalInputGroup}>
                  <Text style={styles.inputLabel}>New Password *</Text>
                  <TextInput
                    value={resetNewPassword}
                    onChangeText={setResetNewPassword}
                    placeholder="At least 6 characters"
                    placeholderTextColor={COLORS.textMuted}
                    secureTextEntry
                    style={styles.modalTextInput}
                  />
                </View>

                <View style={styles.modalInputGroup}>
                  <Text style={styles.inputLabel}>Confirm New Password *</Text>
                  <TextInput
                    value={resetConfirmPassword}
                    onChangeText={setResetConfirmPassword}
                    placeholder="Re-enter new password"
                    placeholderTextColor={COLORS.textMuted}
                    secureTextEntry
                    style={styles.modalTextInput}
                  />
                </View>

                <TouchableOpacity
                  onPress={handleResetPassword}
                  disabled={resetLoading}
                  activeOpacity={0.85}
                  style={[styles.primaryBtn, { marginTop: 12 }, resetLoading && styles.btnDisabled]}
                >
                  {resetLoading ? (
                    <ActivityIndicator color="#ffffff" size="small" />
                  ) : (
                    <Text style={styles.primaryBtnText}>Verify OTP & Reset Password</Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={handleRequestResetOtp}
                  disabled={resetLoading}
                  style={{ marginTop: 14, alignItems: 'center' }}
                >
                  <Text style={{ fontSize: 12, color: COLORS.textSecondary }}>
                    Didn't receive code? <Text style={{ color: COLORS.primary, fontWeight: '700' }}>Resend OTP</Text>
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </KeyboardAvoidingView>
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
    padding: 24,
    maxWidth: 480,
    alignSelf: 'center',
    width: '100%',
  },
  headerBox: {
    alignItems: 'center',
    marginBottom: 20,
  },
  brandLogo: {
    width: 90,
    height: 90,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    elevation: 3,
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
    marginBottom: 16,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 14,
    padding: 12,
    marginBottom: 16,
  },
  errorBannerText: {
    fontSize: 12.5,
    color: '#991B1B',
    lineHeight: 18,
    fontWeight: '600',
  },
  resetPromptLink: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
    textDecorationLine: 'underline',
  },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: 14,
    padding: 12,
    marginBottom: 16,
  },
  successBannerText: {
    fontSize: 12.5,
    color: '#065F46',
    fontWeight: '600',
    flex: 1,
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
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 6,
  },
  forgotText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primaryDark,
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
  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    height: 50,
    marginTop: 8,
  },
  primaryBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ffffff',
  },
  btnDisabled: {
    opacity: 0.65,
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 24,
  },
  footerText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  signupText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    maxWidth: 440,
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 22,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
  },
  modalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  modalHeaderIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: '#E6F4F1',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  modalSubtitle: {
    fontSize: 12.5,
    color: COLORS.textSecondary,
    marginBottom: 14,
    lineHeight: 18,
  },
  closeBtn: {
    padding: 4,
  },
  modalErrorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 10,
    padding: 10,
    marginBottom: 12,
  },
  modalErrorText: {
    fontSize: 12,
    color: '#991B1B',
    fontWeight: '600',
    flex: 1,
  },
  modalInputGroup: {
    marginBottom: 12,
  },
  modalTextInput: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 44,
    fontSize: 13.5,
    color: COLORS.textPrimary,
  },
});
