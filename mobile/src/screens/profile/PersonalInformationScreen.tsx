import React, { useState, useEffect } from 'react';
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
  Modal,
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
  MapPin,
  Building,
  Home,
  ShieldCheck,
  ShieldAlert,
  X,
  Phone,
  CreditCard,
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
  const initialDob = user?.date_of_birth || '';

  // Address initial states
  const initialAddress1 = user?.address_line1 || '';
  const initialAddress2 = user?.address_line2 || '';
  const initialCity = user?.city || '';
  const initialState = user?.state || '';
  const initialPostalCode = user?.postal_code || '';
  const initialCountry = user?.country || 'India';
  const initialAbha = user?.abha_number || '';

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

  // Editable identity fields
  const [fullName, setFullName] = useState(initialName);
  const [phone, setPhone] = useState(initialPhone);
  const [dob, setDob] = useState(initialDob);
  const [profileImageUri, setProfileImageUri] = useState<string | null>(initialAvatar);

  // Editable address fields
  const [addressLine1, setAddressLine1] = useState(initialAddress1);
  const [addressLine2, setAddressLine2] = useState(initialAddress2);
  const [city, setCity] = useState(initialCity);
  const [stateName, setStateName] = useState(initialState);
  const [postalCode, setPostalCode] = useState(initialPostalCode);
  const [country, setCountry] = useState(initialCountry);

  // Editable ABHA Health ID
  const [abhaNumber, setAbhaNumber] = useState(initialAbha);

  // Save operation state
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Email verification modal state
  const isEmailVerified = !!user?.email_verified;
  const [showOtpModal, setShowOtpModal] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [otpSending, setOtpSending] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [otpModalError, setOtpModalError] = useState<string | null>(null);
  const [otpModalSuccess, setOtpModalSuccess] = useState<string | null>(null);
  const [otpCountdown, setOtpCountdown] = useState(0);

  // Resend countdown timer
  useEffect(() => {
    let timer: any;
    if (otpCountdown > 0) {
      timer = setInterval(() => {
        setOtpCountdown((c) => (c > 0 ? c - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [otpCountdown]);

  // Open Email OTP Verification Modal & dispatch code
  const handleOpenEmailVerification = async () => {
    setOtpModalError(null);
    setOtpModalSuccess(null);
    setOtpCode('');
    setShowOtpModal(true);

    setOtpSending(true);
    try {
      const res = await authApi.sendVerificationOtp(initialEmail);
      setOtpModalSuccess(res.message || `A 6-digit verification code has been dispatched to ${initialEmail}.`);
      setOtpCountdown(60);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to dispatch verification code. Please try again.';
      setOtpModalError(msg);
    } finally {
      setOtpSending(false);
    }
  };

  // Resend OTP code
  const handleResendEmailOtp = async () => {
    if (otpCountdown > 0 || otpSending) return;
    setOtpModalError(null);
    setOtpModalSuccess(null);
    setOtpSending(true);
    try {
      const res = await authApi.sendVerificationOtp(initialEmail);
      setOtpModalSuccess(res.message || `A new 6-digit verification code has been dispatched to ${initialEmail}.`);
      setOtpCountdown(60);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to dispatch verification code. Please try again.';
      setOtpModalError(msg);
    } finally {
      setOtpSending(false);
    }
  };

  // Confirm OTP code with backend
  const handleVerifyEmailOtp = async () => {
    const cleanCode = otpCode.trim();
    if (!cleanCode || cleanCode.length !== 6) {
      setOtpModalError('Please enter a valid 6-digit verification code.');
      return;
    }
    setOtpModalError(null);
    setOtpModalSuccess(null);
    setOtpVerifying(true);
    try {
      const res = await authApi.verifyEmailOtp(initialEmail, cleanCode);
      if (user) {
        updateUser({
          ...user,
          email_verified: true,
          is_verified: true,
        });
      }
      setOtpModalSuccess(res.message || 'Email verified successfully!');
      setSuccessMsg('Your email address has been verified successfully!');
      setTimeout(() => {
        setShowOtpModal(false);
        setOtpCode('');
        setOtpModalSuccess(null);
      }, 1500);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid or expired verification code. Please try again.';
      setOtpModalError(msg);
    } finally {
      setOtpVerifying(false);
    }
  };

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

  // Auto-format ABHA ID: 14 digits to XX-XXXX-XXXX-XXXX
  const handleAbhaChange = (text: string) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    const digits = text.replace(/[^0-9]/g, '').slice(0, 14);
    if (digits.length <= 2) {
      setAbhaNumber(digits);
    } else if (digits.length <= 6) {
      setAbhaNumber(`${digits.slice(0, 2)}-${digits.slice(2)}`);
    } else if (digits.length <= 10) {
      setAbhaNumber(`${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6)}`);
    } else {
      setAbhaNumber(
        `${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6, 10)}-${digits.slice(10, 14)}`
      );
    }
  };

  // Check if form has modified changes
  const isDirty =
    fullName.trim() !== initialName ||
    phone.trim() !== initialPhone ||
    dob.trim() !== initialDob ||
    profileImageUri !== initialAvatar ||
    addressLine1.trim() !== initialAddress1 ||
    addressLine2.trim() !== initialAddress2 ||
    city.trim() !== initialCity ||
    stateName.trim() !== initialState ||
    postalCode.trim() !== initialPostalCode ||
    country.trim() !== initialCountry ||
    abhaNumber.trim() !== initialAbha;

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

    if (postalCode.trim() && postalCode.trim().length !== 6) {
      setErrorMsg('Please enter a valid 6-digit postal PIN code.');
      return;
    }

    const rawAbhaDigits = abhaNumber.replace(/[^0-9]/g, '');
    if (rawAbhaDigits.length > 0 && rawAbhaDigits.length !== 14) {
      setErrorMsg('Please enter a valid 14-digit ABHA number (e.g. 91-1234-5678-9012).');
      return;
    }

    setLoading(true);

    try {
      let currentUserData = user;

      // 1. Upload avatar if selected and changed from initial
      if (profileImageUri && profileImageUri !== initialAvatar) {
        currentUserData = await authApi.uploadAvatar(profileImageUri);
      }

      // 2. Update profile text, ABHA ID, and structured address attributes
      const formattedPhone = `+91 ${rawPhoneDigits.slice(0, 5)} ${rawPhoneDigits.slice(5)}`;
      const formattedAbha =
        rawAbhaDigits.length === 14
          ? `${rawAbhaDigits.slice(0, 2)}-${rawAbhaDigits.slice(2, 6)}-${rawAbhaDigits.slice(6, 10)}-${rawAbhaDigits.slice(10, 14)}`
          : initialAbha
          ? ''
          : undefined;

      const updatedUser = await authApi.updateProfile({
        full_name: fullName.trim(),
        phone: formattedPhone,
        date_of_birth: dob.trim() || undefined,
        abha_number: formattedAbha,
        address_line1: addressLine1.trim() || undefined,
        address_line2: addressLine2.trim() || undefined,
        city: city.trim() || undefined,
        state: stateName.trim() || undefined,
        postal_code: postalCode.trim() || undefined,
        country: country.trim() || 'India',
      });

      const mergedUser = { ...(currentUserData || {}), ...updatedUser };
      updateUser(mergedUser);
      setSuccessMsg('Personal profile, ABHA, and address details updated successfully!');
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
        subtitle="Manage your identity, address & verification"
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

          {/* Card 1: Identity & Contact Details */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.cardHeaderIcon}>
                <User size={18} color={COLORS.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Identity & Contact Details</Text>
                <Text style={styles.cardSubtitle}>Your legal profile and primary contact channels</Text>
              </View>
            </View>

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

            {/* 2. Email Address (Account ID - Read-Only) & Verification */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>Email Address</Text>
                {isEmailVerified ? (
                  <View style={styles.emailVerifiedBadge}>
                    <CheckCircle2 size={11} color="#166534" strokeWidth={2.5} style={{ marginRight: 3 }} />
                    <Text style={styles.emailVerifiedText}>Verified</Text>
                  </View>
                ) : (
                  <TouchableOpacity
                    onPress={handleOpenEmailVerification}
                    style={styles.emailUnverifiedBadge}
                    activeOpacity={0.8}
                  >
                    <ShieldAlert size={11} color="#B45309" strokeWidth={2.5} style={{ marginRight: 3 }} />
                    <Text style={styles.emailUnverifiedText}>Unverified • Verify (OTP)</Text>
                  </TouchableOpacity>
                )}
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

              {!isEmailVerified && (
                <TouchableOpacity
                  onPress={handleOpenEmailVerification}
                  style={styles.verifyActionRow}
                  activeOpacity={0.8}
                >
                  <ShieldCheck size={14} color={COLORS.primary} style={{ marginRight: 6 }} />
                  <Text style={styles.verifyActionText}>
                    Tap to verify profile via 6-digit email OTP
                  </Text>
                </TouchableOpacity>
              )}

              <Text style={styles.fieldHint}>
                Your email is your authenticated VitaLens identifier and cannot be modified.
              </Text>
            </View>

            {/* 3. Phone Number (Contact Detail - Numbers do not require verification) */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>Mobile Number</Text>
                <View style={styles.phoneContactPill}>
                  <Phone size={10} color="#0F5C5E" style={{ marginRight: 3 }} />
                  <Text style={styles.phoneContactText}>Primary Contact</Text>
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
              <Text style={styles.fieldHint}>
                Used for SMS appointment alerts and doctor callbacks. Verification not required.
              </Text>
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

          {/* Card 2: Structured Residential Address */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.cardHeaderIcon}>
                <MapPin size={18} color={COLORS.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Residential Address</Text>
                <Text style={styles.cardSubtitle}>
                  Used for diagnostic home sample collections and medicine delivery
                </Text>
              </View>
            </View>

            {/* Address Line 1 */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Address Line 1</Text>
              <View style={styles.inputWrapper}>
                <Home size={18} color={COLORS.primary} style={styles.inputIcon} />
                <TextInput
                  value={addressLine1}
                  onChangeText={(val) => {
                    setAddressLine1(val);
                    setErrorMsg(null);
                  }}
                  placeholder="Flat / House No., Building, Street"
                  placeholderTextColor={COLORS.textMuted}
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* Address Line 2 */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Address Line 2 (Optional)</Text>
              <View style={styles.inputWrapper}>
                <Building size={18} color={COLORS.primary} style={styles.inputIcon} />
                <TextInput
                  value={addressLine2}
                  onChangeText={(val) => {
                    setAddressLine2(val);
                    setErrorMsg(null);
                  }}
                  placeholder="Area, Landmark, Colony"
                  placeholderTextColor={COLORS.textMuted}
                  style={styles.textInput}
                />
              </View>
            </View>

            {/* City & State Row */}
            <View style={styles.rowTwoCols}>
              <View style={[styles.inputGroup, { flex: 1, marginRight: 8 }]}>
                <Text style={styles.inputLabel}>City / District</Text>
                <View style={styles.inputWrapper}>
                  <TextInput
                    value={city}
                    onChangeText={(val) => {
                      setCity(val);
                      setErrorMsg(null);
                    }}
                    placeholder="e.g. Mumbai"
                    placeholderTextColor={COLORS.textMuted}
                    style={styles.textInput}
                  />
                </View>
              </View>

              <View style={[styles.inputGroup, { flex: 1, marginLeft: 8 }]}>
                <Text style={styles.inputLabel}>State / UT</Text>
                <View style={styles.inputWrapper}>
                  <TextInput
                    value={stateName}
                    onChangeText={(val) => {
                      setStateName(val);
                      setErrorMsg(null);
                    }}
                    placeholder="e.g. Maharashtra"
                    placeholderTextColor={COLORS.textMuted}
                    style={styles.textInput}
                  />
                </View>
              </View>
            </View>

            {/* PIN Code & Country Row */}
            <View style={styles.rowTwoCols}>
              <View style={[styles.inputGroup, { flex: 1, marginRight: 8 }]}>
                <Text style={styles.inputLabel}>PIN Code</Text>
                <View style={styles.inputWrapper}>
                  <TextInput
                    value={postalCode}
                    onChangeText={(val) => {
                      const digits = val.replace(/[^0-9]/g, '').slice(0, 6);
                      setPostalCode(digits);
                      setErrorMsg(null);
                    }}
                    placeholder="6 digits"
                    placeholderTextColor={COLORS.textMuted}
                    keyboardType="numeric"
                    maxLength={6}
                    style={styles.textInput}
                  />
                </View>
              </View>

              <View style={[styles.inputGroup, { flex: 1, marginLeft: 8 }]}>
                <Text style={styles.inputLabel}>Country</Text>
                <View style={styles.inputWrapper}>
                  <TextInput
                    value={country}
                    onChangeText={(val) => {
                      setCountry(val);
                      setErrorMsg(null);
                    }}
                    placeholder="India"
                    placeholderTextColor={COLORS.textMuted}
                    style={styles.textInput}
                  />
                </View>
              </View>
            </View>
          </View>

          {/* Card 3: ABHA Health ID (Ayushman Bharat Digital Mission) */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.cardHeaderIcon}>
                <CreditCard size={18} color={COLORS.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>ABHA Health ID</Text>
                <Text style={styles.cardSubtitle}>
                  Ayushman Bharat Digital Mission (ABDM)
                </Text>
              </View>
              {user?.abha_number ? (
                <View style={styles.abhaLinkedBadge}>
                  <CheckCircle2 size={11} color="#166534" strokeWidth={2.5} style={{ marginRight: 3 }} />
                  <Text style={styles.abhaLinkedText}>Linked</Text>
                </View>
              ) : (
                <View style={styles.abhaUnlinkedBadge}>
                  <Text style={styles.abhaUnlinkedText}>Not Linked</Text>
                </View>
              )}
            </View>

            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>14-Digit ABHA ID</Text>
                {abhaNumber.length > 0 && (
                  <TouchableOpacity
                    onPress={() => {
                      setAbhaNumber('');
                      setErrorMsg(null);
                    }}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.clearAbhaText}>Clear</Text>
                  </TouchableOpacity>
                )}
              </View>
              <View style={styles.inputWrapper}>
                <CreditCard size={18} color={COLORS.primary} style={styles.inputIcon} />
                <TextInput
                  value={abhaNumber}
                  onChangeText={handleAbhaChange}
                  placeholder="91-1234-5678-9012"
                  placeholderTextColor={COLORS.textMuted}
                  keyboardType="numeric"
                  maxLength={17}
                  style={[styles.textInput, { letterSpacing: 1.2, fontWeight: '700' }]}
                />
              </View>
              <Text style={styles.fieldHint}>
                Format: XX-XXXX-XXXX-XXXX. Links your government health records securely.
              </Text>
            </View>

            <View style={styles.abhaInfoBox}>
              <ShieldCheck size={16} color={COLORS.primary} style={{ marginRight: 8, marginTop: 1 }} />
              <Text style={styles.abhaInfoText}>
                Your Ayushman Bharat Health Account (ABHA) connects your VitaLens health insights with authorized healthcare providers, laboratories, and hospitals nationwide.
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

      {/* Email Verification OTP Modal */}
      <Modal
        visible={showOtpModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => {
          if (!otpVerifying) setShowOtpModal(false);
        }}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.modalOverlay}
        >
          <View style={styles.modalCard}>
            {/* Header */}
            <View style={styles.modalHeaderRow}>
              <View style={styles.modalHeaderIconBox}>
                <Mail size={22} color={COLORS.primary} strokeWidth={2.2} />
              </View>
              <TouchableOpacity
                onPress={() => setShowOtpModal(false)}
                disabled={otpVerifying}
                style={styles.modalCloseBtn}
                activeOpacity={0.7}
              >
                <X size={20} color="#64748B" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalTitle}>Verify Email Address</Text>
            <Text style={styles.modalSubtitle}>
              Enter the 6-digit verification code sent to:
            </Text>
            <Text style={styles.modalEmailHighlight}>{initialEmail}</Text>

            {/* Feedback Messages */}
            {otpModalError && (
              <View style={styles.modalErrorBanner}>
                <AlertCircle size={15} color={COLORS.danger} style={{ marginRight: 6 }} />
                <Text style={styles.modalErrorText}>{otpModalError}</Text>
              </View>
            )}

            {otpModalSuccess && (
              <View style={styles.modalSuccessBanner}>
                <CheckCircle2 size={15} color={COLORS.success} style={{ marginRight: 6 }} />
                <Text style={styles.modalSuccessText}>{otpModalSuccess}</Text>
              </View>
            )}

            {/* OTP Code Input */}
            <View style={styles.otpInputBox}>
              <TextInput
                value={otpCode}
                onChangeText={(val) => {
                  setOtpCode(val.replace(/[^0-9]/g, '').slice(0, 6));
                  setOtpModalError(null);
                }}
                placeholder="• • • • • •"
                placeholderTextColor="#94A3B8"
                keyboardType="numeric"
                maxLength={6}
                autoFocus={true}
                style={styles.otpTextInput}
              />
            </View>

            {/* Resend Action */}
            <View style={styles.resendRow}>
              <Text style={styles.resendPrompt}>Didn't receive the code? </Text>
              {otpCountdown > 0 ? (
                <Text style={styles.resendCountdown}>Resend in {otpCountdown}s</Text>
              ) : (
                <TouchableOpacity
                  onPress={handleResendEmailOtp}
                  disabled={otpSending || otpVerifying}
                  style={styles.resendBtn}
                >
                  {otpSending ? (
                    <ActivityIndicator size="small" color={COLORS.primary} />
                  ) : (
                    <Text style={styles.resendBtnText}>Resend Code</Text>
                  )}
                </TouchableOpacity>
              )}
            </View>

            {/* Verify Button */}
            <TouchableOpacity
              onPress={handleVerifyEmailOtp}
              disabled={otpCode.length !== 6 || otpVerifying}
              style={[
                styles.modalVerifyBtn,
                (otpCode.length !== 6 || otpVerifying) && styles.modalVerifyBtnDisabled,
              ]}
              activeOpacity={0.85}
            >
              {otpVerifying ? (
                <ActivityIndicator size="small" color="#ffffff" />
              ) : (
                <>
                  <ShieldCheck size={18} color="#ffffff" strokeWidth={2.2} style={{ marginRight: 8 }} />
                  <Text style={styles.modalVerifyBtnText}>Verify Email</Text>
                </>
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
  // Card
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 18,
    boxShadow: '0px 2px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  cardHeaderIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#E0ECE7',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#0F172A',
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  inputGroup: {
    marginBottom: 14,
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
  emailVerifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 2.5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#86EFAC',
  },
  emailVerifiedText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#166534',
    letterSpacing: 0.2,
  },
  emailUnverifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 2.5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  emailUnverifiedText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#92400E',
    letterSpacing: 0.2,
  },
  phoneContactPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDFA',
    paddingHorizontal: 8,
    paddingVertical: 2.5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#CCFBF1',
  },
  phoneContactText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0F5C5E',
  },
  ageBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.primary,
  },
  abhaLinkedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#86EFAC',
  },
  abhaLinkedText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#166534',
  },
  abhaUnlinkedBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  abhaUnlinkedText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
  },
  clearAbhaText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.danger,
  },
  abhaInfoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#CCFBF1',
    borderRadius: 12,
    padding: 12,
    marginTop: 4,
  },
  abhaInfoText: {
    flex: 1,
    fontSize: 12,
    color: '#0F5C5E',
    lineHeight: 17,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 14,
    height: 48,
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
  verifyActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E0ECE7',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    marginTop: 8,
  },
  verifyActionText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  rowTwoCols: {
    flexDirection: 'row',
    justifyContent: 'space-between',
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
    marginTop: 4,
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
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  modalCard: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 24,
    boxShadow: '0px 10px 25px rgba(0, 0, 0, 0.2)',
    elevation: 6,
  },
  modalHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  modalHeaderIconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#E0ECE7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalCloseBtn: {
    padding: 6,
  },
  modalTitle: {
    fontSize: 19,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 13,
    color: '#64748B',
  },
  modalEmailHighlight: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: 16,
  },
  modalErrorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.dangerLight,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    marginBottom: 14,
  },
  modalErrorText: {
    fontSize: 12,
    color: COLORS.danger,
    fontWeight: '600',
    flex: 1,
  },
  modalSuccessBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.successLight,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    marginBottom: 14,
  },
  modalSuccessText: {
    fontSize: 12,
    color: COLORS.success,
    fontWeight: '600',
    flex: 1,
  },
  otpInputBox: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    borderRadius: 16,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  otpTextInput: {
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: 8,
    textAlign: 'center',
    color: '#0F172A',
    width: '100%',
  },
  resendRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  resendPrompt: {
    fontSize: 13,
    color: '#64748B',
  },
  resendCountdown: {
    fontSize: 13,
    fontWeight: '700',
    color: '#94A3B8',
  },
  resendBtn: {
    paddingVertical: 2,
    paddingHorizontal: 4,
  },
  resendBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primary,
  },
  modalVerifyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    height: 50,
  },
  modalVerifyBtnDisabled: {
    backgroundColor: '#94A3B8',
    opacity: 0.6,
  },
  modalVerifyBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
});
