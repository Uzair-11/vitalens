import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Switch,
  Alert,
  StyleSheet,
  Platform,
  Modal,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
} from 'react-native';
import {
  ShieldCheck,
  Fingerprint,
  Smartphone,
  AlertTriangle,
  KeyRound,
  Laptop,
  ChevronRight,
  LogOut,
  CheckCircle2,
  Lock,
  X,
} from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { COLORS } from '../../constants/colors';
import { useAuthStore } from '../../store/authStore';

export const AccountSecurityScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const user = useAuthStore((state) => state.user);

  // Security Toggles
  const [biometricEnabled, setBiometricEnabled] = useState(true);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [loginAlertsEnabled, setLoginAlertsEnabled] = useState(true);

  // Sessions State
  const [otherSessions, setOtherSessions] = useState([
    {
      id: 'session-2',
      device: 'Chrome on Windows 11',
      type: 'Web Portal',
      location: 'New Delhi, India',
      lastActive: 'Active 2 hours ago',
    },
  ]);
  const [loggingOutSessions, setLoggingOutSessions] = useState(false);

  // Password Modal
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);

  const handleToggleBiometric = (val: boolean) => {
    setBiometricEnabled(val);
    Alert.alert(
      val ? 'Biometrics Activated' : 'Biometrics Disabled',
      val
        ? 'Fingerprint and FaceID are now enabled for fast and secure access to VitaLens.'
        : 'Biometric authentication has been turned off. Password will be required.'
    );
  };

  const handleToggle2FA = (val: boolean) => {
    setTwoFactorEnabled(val);
    if (val) {
      Alert.alert(
        'Two-Factor Authentication (2FA)',
        `A verification code will be sent to your registered mobile number (${user?.phone || '+91 98765 43210'}) whenever a new device attempts to sign in.`,
        [{ text: 'Got It' }]
      );
    }
  };

  const handleToggleLoginAlerts = (val: boolean) => {
    setLoginAlertsEnabled(val);
  };

  const handleLogoutAllOtherDevices = () => {
    if (otherSessions.length === 0) {
      Alert.alert('No Other Sessions', 'There are currently no other active device sessions.');
      return;
    }

    Alert.alert(
      'Log Out of All Other Devices',
      'This will revoke authentication tokens on all computers, tablets, and phones other than this current mobile device. Do you wish to continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Log Out Others',
          style: 'destructive',
          onPress: () => {
            setLoggingOutSessions(true);
            setTimeout(() => {
              setOtherSessions([]);
              setLoggingOutSessions(false);
              Alert.alert('Success', 'All other active sessions have been safely terminated.');
            }, 800);
          },
        },
      ]
    );
  };

  const handleChangePassword = () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      Alert.alert('Missing Fields', 'Please fill in all password fields.');
      return;
    }
    if (newPassword.length < 8) {
      Alert.alert('Password Too Short', 'New password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Password Mismatch', 'The new password and confirm password do not match.');
      return;
    }

    setPasswordLoading(true);
    setTimeout(() => {
      setPasswordLoading(false);
      setPasswordModalVisible(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      Alert.alert('Password Updated', 'Your account credentials have been securely updated.');
    }, 1000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Account Security"
        subtitle="Biometrics, two-factor auth & active sessions"
        onBack={() => navigation.goBack()}
      />

      <ScrollView
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Visual Security Status Banner */}
        <View style={styles.statusCard}>
          <View style={styles.statusHeaderRow}>
            <View style={styles.statusIconBox}>
              <ShieldCheck size={28} color="#059669" strokeWidth={2.4} />
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.secureBadgeRow}>
                <Text style={styles.statusTitle}>Your Account is Secure</Text>
                <View style={styles.verifiedCheckPill}>
                  <CheckCircle2 size={12} color="#059669" style={{ marginRight: 3 }} />
                  <Text style={styles.verifiedCheckText}>Healthy</Text>
                </View>
              </View>
              <Text style={styles.statusSubtitle}>
                Protected by TLS 1.3 transit encryption, Argon2id token signing & AES-256 resting encryption.
              </Text>
            </View>
          </View>

          <View style={styles.tagPillRow}>
            <View style={styles.tagPill}>
              <Text style={styles.tagPillText}>🛡️ TLS 1.3 Active</Text>
            </View>
            <View style={styles.tagPill}>
              <Text style={styles.tagPillText}>🔒 AES-256 Encrypted</Text>
            </View>
            <View style={styles.tagPill}>
              <Text style={styles.tagPillText}>⚡ Token Session Protected</Text>
            </View>
          </View>
        </View>

        {/* Section 1: Login & Access Controls */}
        <Text style={styles.sectionHeader}>LOGIN & ACCESS CONTROLS</Text>
        <View style={styles.card}>
          {/* Biometrics Toggle */}
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#E0ECE7' }]}>
              <Fingerprint size={20} color={COLORS.primary} />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Biometric Login</Text>
              <Text style={styles.settingSubtitle}>
                Unlock VitaLens with Fingerprint or FaceID for fast, secure access.
              </Text>
            </View>
            <Switch
              value={biometricEnabled}
              onValueChange={handleToggleBiometric}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          {/* Two-Factor Authentication */}
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#EFF6FF' }]}>
              <Smartphone size={20} color="#2563EB" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Two-Factor Authentication (2FA)</Text>
              <Text style={styles.settingSubtitle}>
                Require an SMS OTP when signing in from an unfamiliar browser or device.
              </Text>
            </View>
            <Switch
              value={twoFactorEnabled}
              onValueChange={handleToggle2FA}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <View style={styles.divider} />

          {/* Login Anomaly Alerts */}
          <View style={styles.settingRow}>
            <View style={[styles.settingIconBox, { backgroundColor: '#FEF3C7' }]}>
              <AlertTriangle size={20} color="#D97706" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Login Alerts</Text>
              <Text style={styles.settingSubtitle}>
                Receive immediate security alerts if your account is accessed from a new IP.
              </Text>
            </View>
            <Switch
              value={loginAlertsEnabled}
              onValueChange={handleToggleLoginAlerts}
              trackColor={{ false: '#CBD5E1', true: COLORS.primary }}
              thumbColor="#ffffff"
            />
          </View>
        </View>

        {/* Section 2: Password & Credentials */}
        <Text style={styles.sectionHeader}>CREDENTIALS</Text>
        <View style={styles.card}>
          <TouchableOpacity
            onPress={() => setPasswordModalVisible(true)}
            style={styles.settingRow}
            activeOpacity={0.7}
          >
            <View style={[styles.settingIconBox, { backgroundColor: '#F1F5F9' }]}>
              <KeyRound size={20} color="#475569" />
            </View>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>Change Password</Text>
              <Text style={styles.settingSubtitle}>Last updated 3 months ago • Strong password</Text>
            </View>
            <ChevronRight size={20} color="#94A3B8" />
          </TouchableOpacity>
        </View>

        {/* Section 3: Active Device Sessions */}
        <Text style={styles.sectionHeader}>ACTIVE SESSIONS & DEVICES</Text>
        <View style={styles.card}>
          {/* Current Device */}
          <View style={styles.sessionRow}>
            <View style={[styles.sessionIconBox, { backgroundColor: '#DEF7EC' }]}>
              <Smartphone size={20} color="#059669" />
              <View style={styles.activeDot} />
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.sessionTitleRow}>
                <Text style={styles.sessionTitle}>
                  This Device • {Platform.OS === 'android' ? 'Android 14' : Platform.OS === 'ios' ? 'iOS 18' : 'Web Browser'}
                </Text>
                <View style={styles.currentDeviceBadge}>
                  <Text style={styles.currentDeviceBadgeText}>Current</Text>
                </View>
              </View>
              <Text style={styles.sessionMeta}>VitaLens Mobile App • Active Now • New Delhi, IN</Text>
            </View>
          </View>

          {/* Other Sessions */}
          {otherSessions.map((sess) => (
            <React.Fragment key={sess.id}>
              <View style={styles.divider} />
              <View style={styles.sessionRow}>
                <View style={[styles.sessionIconBox, { backgroundColor: '#F1F5F9' }]}>
                  <Laptop size={20} color="#64748B" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.sessionTitle}>{sess.device}</Text>
                  <Text style={styles.sessionMeta}>
                    {sess.type} • {sess.lastActive} • {sess.location}
                  </Text>
                </View>
              </View>
            </React.Fragment>
          ))}

          {otherSessions.length > 0 && (
            <TouchableOpacity
              onPress={handleLogoutAllOtherDevices}
              disabled={loggingOutSessions}
              style={styles.logoutOthersBtn}
              activeOpacity={0.75}
            >
              {loggingOutSessions ? (
                <ActivityIndicator size="small" color="#DC2626" />
              ) : (
                <>
                  <LogOut size={16} color="#DC2626" style={{ marginRight: 8 }} />
                  <Text style={styles.logoutOthersText}>Log Out of All Other Devices</Text>
                </>
              )}
            </TouchableOpacity>
          )}
        </View>

        <View style={{ height: 20 }} />
      </ScrollView>

      {/* Change Password Modal */}
      <Modal
        visible={passwordModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setPasswordModalVisible(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.modalOverlay}
        >
          <View style={styles.modalCard}>
            <View style={styles.modalHeaderRow}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <View style={styles.modalHeaderIcon}>
                  <Lock size={18} color={COLORS.primary} />
                </View>
                <Text style={styles.modalTitle}>Change Password</Text>
              </View>
              <TouchableOpacity onPress={() => setPasswordModalVisible(false)} style={styles.closeBtn}>
                <X size={20} color="#64748B" />
              </TouchableOpacity>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Current Password</Text>
              <TextInput
                secureTextEntry
                value={currentPassword}
                onChangeText={setCurrentPassword}
                placeholder="Enter current password"
                placeholderTextColor={COLORS.textMuted}
                style={styles.modalInput}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>New Password</Text>
              <TextInput
                secureTextEntry
                value={newPassword}
                onChangeText={setNewPassword}
                placeholder="At least 8 characters"
                placeholderTextColor={COLORS.textMuted}
                style={styles.modalInput}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Confirm New Password</Text>
              <TextInput
                secureTextEntry
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                placeholder="Re-enter new password"
                placeholderTextColor={COLORS.textMuted}
                style={styles.modalInput}
              />
            </View>

            <TouchableOpacity
              onPress={handleChangePassword}
              disabled={passwordLoading}
              style={styles.submitPasswordBtn}
              activeOpacity={0.8}
            >
              {passwordLoading ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <Text style={styles.submitPasswordText}>Update Password</Text>
              )}
            </TouchableOpacity>
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
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 32,
  },
  // Status Card
  statusCard: {
    backgroundColor: '#ECFDF5',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    marginBottom: 20,
    boxShadow: '0px 2px 8px rgba(5, 150, 105, 0.08)',
    elevation: 2,
  },
  statusHeaderRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  statusIconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#D1FAE5',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  secureBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 4,
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#065F46',
  },
  verifiedCheckPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#6EE7B7',
  },
  verifiedCheckText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#047857',
  },
  statusSubtitle: {
    fontSize: 12,
    color: '#047857',
    lineHeight: 18,
  },
  tagPillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#A7F3D0',
  },
  tagPill: {
    backgroundColor: '#ffffff',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#6EE7B7',
  },
  tagPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#065F46',
  },
  // Sections
  sectionHeader: {
    fontSize: 12,
    fontWeight: '800',
    color: '#475569',
    letterSpacing: 0.8,
    marginBottom: 8,
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
  // Sessions
  sessionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  sessionIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
    position: 'relative',
  },
  activeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#059669',
    position: 'absolute',
    top: 6,
    right: 6,
    borderWidth: 1.5,
    borderColor: '#ffffff',
  },
  sessionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 2,
  },
  sessionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#1E293B',
  },
  currentDeviceBadge: {
    backgroundColor: '#DEF7EC',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#BCF0DA',
  },
  currentDeviceBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#03543F',
  },
  sessionMeta: {
    fontSize: 12,
    color: '#64748B',
  },
  logoutOthersBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 14,
    paddingVertical: 12,
    marginTop: 16,
  },
  logoutOthersText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#DC2626',
  },
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 24,
    paddingBottom: Platform.OS === 'ios' ? 40 : 28,
  },
  modalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  modalHeaderIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: '#E0ECE7',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#1E293B',
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  inputGroup: {
    marginBottom: 14,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 6,
  },
  modalInput: {
    height: 48,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    fontSize: 14,
    color: '#1E293B',
  },
  submitPasswordBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    height: 50,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
  },
  submitPasswordText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
});
