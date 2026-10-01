import React from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, TouchableOpacity, ScrollView, Alert, Platform, StyleSheet, Image } from 'react-native';
import {
  User,
  Shield,
  Bell,
  Lock,
  FileText,
  ChevronRight,
  LogOut,
  Info,
  Heart,
  ShieldAlert,
} from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { useAuthStore } from '../../store/authStore';
import { COLORS } from '../../constants/colors';
import { getMediaUrl } from '../../constants/config';

interface MenuItem {
  title: string;
  subtitle: string;
  icon: any;
  iconBg: string;
  iconColor: string;
  action: () => void;
}

interface MenuSection {
  sectionTitle: string;
  items: MenuItem[];
}

export const ProfileScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      if (window.confirm('Are you sure you want to sign out of VitaLens?')) {
        logout();
      }
    } else {
      Alert.alert('Sign Out', 'Are you sure you want to sign out of VitaLens?', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Sign Out', style: 'destructive', onPress: () => logout() },
      ]);
    }
  };

  const sections: MenuSection[] = [
    {
      sectionTitle: 'HEALTH PROFILE',
      items: [
        {
          title: 'Personal Information',
          subtitle: 'Name, email & verified mobile number',
          icon: User,
          iconBg: '#E0ECE7',
          iconColor: '#0F5C5E',
          action: () => navigation.navigate('PersonalInformation'),
        },
        {
          title: 'Medical Information',
          subtitle: 'Blood group, vitals & emergency contact',
          icon: Heart,
          iconBg: '#FEE2E2',
          iconColor: '#DC2626',
          action: () => navigation.navigate('MedicalInformation'),
        },
      ],
    },
    {
      sectionTitle: 'ACCOUNT & SECURITY',
      items: [
        {
          title: 'Security',
          subtitle: 'Biometrics, 2FA & active sessions',
          icon: Lock,
          iconBg: '#EFF6FF',
          iconColor: '#2563EB',
          action: () => navigation.navigate('AccountSecurity'),
        },
        {
          title: 'Notifications',
          subtitle: 'Granular delivery channels & alerts',
          icon: Bell,
          iconBg: '#FEF3C7',
          iconColor: '#D97706',
          action: () => navigation.navigate('NotificationPreferences'),
        },
        {
          title: 'Privacy & Data Protection',
          subtitle: 'Consent controls & HIPAA/DPDP rights',
          icon: Shield,
          iconBg: '#F5F3FF',
          iconColor: '#7C3AED',
          action: () => navigation.navigate('PrivacyConsent'),
        },
      ],
    },
    {
      sectionTitle: 'SUPPORT & LEGAL',
      items: [
        {
          title: 'Clinical Safety Notice',
          subtitle: 'Clinical AI scope & regulatory disclaimers',
          icon: ShieldAlert,
          iconBg: '#F0FDFA',
          iconColor: '#0F5C5E',
          action: () => navigation.navigate('ClinicalDisclaimer'),
        },
        {
          title: 'About VitaLens',
          subtitle: 'App version 1.0.0 & platform overview',
          icon: Info,
          iconBg: '#ECFDF5',
          iconColor: '#059669',
          action: () =>
            Alert.alert(
              'About VitaLens',
              'VitaLens v1.0.0\nUnderstand today, healthier tomorrow.\nAI Health Report Analysis & Doctor Recommendation System.'
            ),
        },
      ],
    },
  ];

  const fullName = user?.full_name || 'Uzair Shaikh';
  const email = user?.email || 'uzair@example.com';
  const phone = user?.phone || '+91 98765 43210';
  const initial = fullName.charAt(0).toUpperCase();
  const avatarUrl = getMediaUrl(user?.avatar_url);

  const userRole = (
    user?.role ||
    (user?.email?.startsWith('admin@') || user?.full_name?.toLowerCase().includes('administrator') ? 'ADMIN' : 'PATIENT')
  ).toUpperCase();

  const getRoleBadgeStyle = (r: string) => {
    switch (r) {
      case 'ADMIN':
      case 'SUPER_ADMIN':
        return { bg: '#FEE2E2', text: '#DC2626' };
      case 'DOCTOR':
        return { bg: '#E0E7FF', text: '#4338CA' };
      case 'SUPPORT_STAFF':
        return { bg: '#FEF3C7', text: '#D97706' };
      default:
        return { bg: '#E0F2FE', text: '#0369A1' };
    }
  };
  const roleStyle = getRoleBadgeStyle(userRole);


  return (
    <SafeAreaView style={styles.container}>
      <Header title="My Profile" subtitle="Account, health profile & settings" showLogo />

      <ScrollView style={styles.scrollArea} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Compact Horizontal User Identity Card */}
        <View style={styles.userCard}>
          {avatarUrl ? (
            <Image source={{ uri: avatarUrl }} style={styles.avatarImg} />
          ) : (
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarInitial}>{initial}</Text>
            </View>
          )}
          <View style={styles.userInfo}>
            <View style={styles.nameBadgeRow}>
              <Text style={styles.userName} numberOfLines={1}>{fullName}</Text>
              <View style={[styles.roleBadge, { backgroundColor: roleStyle.bg }]}>
                <Text style={[styles.roleBadgeText, { color: roleStyle.text }]}>{userRole}</Text>
              </View>
            </View>
            <Text style={styles.userEmail} numberOfLines={1}>{email}</Text>
            <Text style={styles.userPhone} numberOfLines={1}>{phone}</Text>
          </View>
        </View>


        {/* Categorized Settings & Profile Lists */}
        {sections.map((section) => (
          <View key={section.sectionTitle} style={styles.sectionContainer}>
            <Text style={styles.sectionHeader}>{section.sectionTitle}</Text>
            <View style={styles.menuContainer}>
              {section.items.map((item, index) => {
                const IconComponent = item.icon;
                const isLast = index === section.items.length - 1;
                return (
                  <TouchableOpacity
                    key={item.title}
                    onPress={item.action}
                    style={[styles.menuRow, isLast && styles.menuRowLast]}
                    activeOpacity={0.7}
                  >
                    <View style={styles.menuLeft}>
                      <View style={[styles.menuIconBox, { backgroundColor: item.iconBg }]}>
                        <IconComponent size={18} color={item.iconColor} strokeWidth={2.2} />
                      </View>
                      <View style={styles.menuTextContainer}>
                        <Text style={styles.menuTitle}>{item.title}</Text>
                        <Text style={styles.menuSubtitle} numberOfLines={1}>{item.subtitle}</Text>
                      </View>
                    </View>
                    <ChevronRight size={19} color="#475569" strokeWidth={2.4} />
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        ))}

        {/* Refined Destructive Sign Out Button */}
        <TouchableOpacity
          onPress={handleLogout}
          style={styles.signOutBtn}
          activeOpacity={0.8}
        >
          <LogOut size={18} color="#DC2626" strokeWidth={2.2} style={{ marginRight: 8 }} />
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
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
    paddingBottom: 28,
  },
  // Compact Horizontal User Card
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 20,
    boxShadow: '0px 2px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
  },
  avatarCircle: {
    width: 60,
    height: 60,
    borderRadius: 20,
    backgroundColor: '#E0ECE7',
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  avatarImg: {
    width: 60,
    height: 60,
    borderRadius: 20,
    marginRight: 16,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  avatarInitial: {
    fontSize: 24,
    fontWeight: '900',
    color: COLORS.primaryDark,
  },
  userInfo: {
    flex: 1,
    justifyContent: 'center',
  },
  nameBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 2,
    flexWrap: 'wrap',
    gap: 8,
  },
  userName: {
    fontSize: 17,
    fontWeight: '800',
    color: '#1E293B',
  },
  roleBadge: {
    backgroundColor: '#E0F2FE',
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
  },
  roleBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0369A1',
    letterSpacing: 0.4,
  },
  userEmail: {
    fontSize: 13,
    fontWeight: '500',
    color: '#4A4A4A',
    marginBottom: 2,
  },
  userPhone: {
    fontSize: 12,
    fontWeight: '600',
    color: '#555555',
  },
  // Section Headers & Lists
  sectionContainer: {
    marginBottom: 18,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '800',
    color: '#4A4A4A',
    letterSpacing: 0.6,
    marginBottom: 8,
    marginLeft: 4,
  },
  menuContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    overflow: 'hidden',
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
  },
  menuRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  menuRowLast: {
    borderBottomWidth: 0,
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 10,
  },
  menuIconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  menuTextContainer: {
    flex: 1,
  },
  menuTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
  },
  menuSubtitle: {
    fontSize: 12,
    fontWeight: '500',
    color: '#4A4A4A',
    marginTop: 2,
  },
  // Distinct Destructive Sign Out Button
  signOutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEF2F2',
    borderWidth: 1.5,
    borderColor: '#FECACA',
    borderRadius: 16,
    height: 52,
    marginTop: 8,
    marginBottom: 16,
    boxShadow: '0px 2px 6px rgba(220, 38, 38, 0.08)',
    elevation: 1,
  },
  signOutText: {
    color: '#DC2626',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
});

