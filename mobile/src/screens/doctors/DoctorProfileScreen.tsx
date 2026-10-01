import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  Image,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { Star, Award, MapPin, Globe, Calendar, ArrowRight } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { Button } from '../../components/common/Button';
import { doctorApi } from '../../api/doctorApi';
import { Doctor } from '../../types';
import { useReportWizardStore } from '../../store/reportWizardStore';
import { COLORS } from '../../constants/colors';

export const DoctorProfileScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { doctorId } = route.params;
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [loading, setLoading] = useState(true);
  const setSelectedDoctor = useReportWizardStore((state) => state.setSelectedDoctor);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        const data = await doctorApi.getDoctorDetail(doctorId);
        setDoctor(data);
        setSelectedDoctor(data);
      } catch (e) {
        console.warn('Error fetching doctor:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
  }, [doctorId]);

  const handleBookNow = () => {
    if (doctor) {
      setSelectedDoctor(doctor);
      navigation.navigate('SlotSelection', { doctorId: doctor.id });
    }
  };

  if (loading || !doctor) {
    return (
      <SafeAreaView style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Header title="Doctor Profile" onBack={() => navigation.goBack()} />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Profile Card Header */}
        <View style={styles.profileCard}>
          <Image
            source={{
              uri:
                doctor.profile_photo_url ||
                'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&q=80&w=300',
            }}
            style={styles.doctorAvatar}
          />
          <Text style={styles.doctorName}>{doctor.full_name}</Text>
          <Text style={styles.specialtyName}>{doctor.specialty_name}</Text>

          {/* Metric Stats Row */}
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <View style={styles.ratingRow}>
                <Star size={13} color={COLORS.attention} fill={COLORS.attention} />
                <Text style={styles.ratingValue}>{doctor.rating}</Text>
              </View>
              <Text style={styles.statLabel}>{doctor.review_count} reviews</Text>
            </View>

            <View style={[styles.statItem, styles.statItemBorder]}>
              <View style={styles.ratingRow}>
                <Award size={14} color={COLORS.primary} />
                <Text style={styles.statValue}>{doctor.experience_years} yrs</Text>
              </View>
              <Text style={styles.statLabel}>Experience</Text>
            </View>

            <View style={styles.statItem}>
              <Text style={styles.feeValue}>₹{doctor.consultation_fee}</Text>
              <Text style={styles.statLabel}>Consultation</Text>
            </View>
          </View>
        </View>

        {/* About Section */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionHeading}>About</Text>
          <Text style={styles.bodyText}>{doctor.bio}</Text>
        </View>

        {/* Qualifications Section */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionHeading}>Qualifications</Text>
          <Text style={styles.bodyText}>• {doctor.qualification}</Text>
        </View>

        {/* Clinic Location & Languages */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionHeading}>Clinic & Practice</Text>

          <View style={styles.infoRow}>
            <MapPin size={16} color={COLORS.primary} style={{ marginTop: 2 }} />
            <View style={{ marginLeft: 10, flex: 1 }}>
              <Text style={styles.clinicTitle}>{doctor.clinic_name}</Text>
              <Text style={styles.clinicAddress}>
                {doctor.address}, {doctor.city}
              </Text>
            </View>
          </View>

          {doctor.languages && doctor.languages.length > 0 && (
            <View style={[styles.infoRow, styles.languagesRow]}>
              <Globe size={16} color={COLORS.secondary} />
              <Text style={styles.languagesText}>
                Languages: <Text style={styles.boldText}>{doctor.languages.join(' · ')}</Text>
              </Text>
            </View>
          )}
        </View>

        {/* View Available Slots CTA */}
        <Button
          title="View Available Slots"
          onPress={handleBookNow}
          icon={<Calendar size={18} color="#ffffff" />}
          size="lg"
          style={{ marginBottom: 24 }}
        />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollArea: {
    padding: 20,
  },
  profileCard: {
    backgroundColor: COLORS.surface,
    padding: 24,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    alignItems: 'center',
    marginBottom: 16,
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
  },
  doctorAvatar: {
    width: 90,
    height: 90,
    borderRadius: 24,
    backgroundColor: COLORS.background,
    marginBottom: 12,
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },
  doctorName: {
    fontSize: 20,
    fontWeight: '900',
    color: COLORS.textPrimary,
    textAlign: 'center',
  },
  specialtyName: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primary,
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginTop: 18,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statItemBorder: {
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: COLORS.borderSubtle,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingValue: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginLeft: 4,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginLeft: 4,
  },
  feeValue: {
    fontSize: 15,
    fontWeight: '900',
    color: COLORS.primaryDark,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  sectionCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 14,
  },
  sectionHeading: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 8,
  },
  bodyText: {
    fontSize: 13,
    color: COLORS.textPrimary,
    lineHeight: 19,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  clinicTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  clinicAddress: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  languagesRow: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
    alignItems: 'center',
  },
  languagesText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginLeft: 10,
  },
  boldText: {
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
});
