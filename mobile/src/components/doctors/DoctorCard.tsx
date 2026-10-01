import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { Star, Award, MapPin, ChevronRight, Clock } from 'lucide-react-native';
import { Doctor } from '../../types';
import { COLORS } from '../../constants/colors';

interface DoctorCardProps {
  doctor: Doctor;
  onPress: () => void;
}

export const DoctorCard: React.FC<DoctorCardProps> = ({ doctor, onPress }) => {
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.85}
      style={styles.cardContainer}
    >
      <View style={styles.topRow}>
        <Image
          source={{
            uri:
              doctor.profile_photo_url ||
              'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&q=80&w=200',
          }}
          style={styles.doctorAvatar}
        />

        <View style={styles.infoBox}>
          <View style={styles.nameRow}>
            <Text style={styles.doctorName}>{doctor.full_name}</Text>
            <View style={styles.ratingBadge}>
              <Star size={11} color={COLORS.attention} fill={COLORS.attention} style={{ marginRight: 3 }} />
              <Text style={styles.ratingText}>{doctor.rating}</Text>
            </View>
          </View>

          <Text style={styles.specialtyText}>{doctor.specialty_name || 'Medical Specialist'}</Text>
          <Text style={styles.qualificationText} numberOfLines={1}>
            {doctor.qualification}
          </Text>
        </View>
      </View>

      {/* Footer Info Row */}
      <View style={styles.footerRow}>
        <View style={styles.footerItem}>
          <Award size={13} color={COLORS.primary} />
          <Text style={styles.footerItemText}>{doctor.experience_years} yrs exp</Text>
        </View>

        <View style={[styles.footerItem, { flex: 1, marginHorizontal: 8 }]}>
          <MapPin size={13} color={COLORS.textSecondary} />
          <Text style={styles.footerItemText} numberOfLines={1}>
            {doctor.clinic_name}
          </Text>
        </View>

        <View style={styles.priceBox}>
          <Text style={styles.feeText}>₹{doctor.consultation_fee}</Text>
          <ChevronRight size={14} color={COLORS.textMuted} style={{ marginLeft: 4 }} />
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  doctorAvatar: {
    width: 58,
    height: 58,
    borderRadius: 16,
    backgroundColor: COLORS.background,
    marginRight: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  infoBox: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  doctorName: {
    fontSize: 15,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  ratingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.attentionLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#F7E2B5',
  },
  ratingText: {
    fontSize: 11,
    fontWeight: '800',
    color: COLORS.attention,
  },
  specialtyText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
    marginTop: 2,
  },
  qualificationText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  footerItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  footerItemText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    fontWeight: '500',
    marginLeft: 4,
  },
  priceBox: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  feeText: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.primaryDark,
  },
});
