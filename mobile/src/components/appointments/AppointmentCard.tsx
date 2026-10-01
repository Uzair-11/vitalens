import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
import { Calendar, Clock, MapPin, XCircle } from 'lucide-react-native';
import { Appointment } from '../../types';
import { COLORS } from '../../constants/colors';

interface AppointmentCardProps {
  appointment: Appointment;
  onCancel?: (appointmentId: string) => void;
  onReschedule?: (appointment: Appointment) => void;
}

export const AppointmentCard: React.FC<AppointmentCardProps> = ({
  appointment,
  onCancel,
}) => {
  const getStatusBadge = () => {
    switch (appointment.status) {
      case 'CONFIRMED':
        return (
          <View style={[styles.statusBadge, styles.confirmedBadge]}>
            <Text style={[styles.statusText, styles.confirmedText]}>CONFIRMED</Text>
          </View>
        );
      case 'COMPLETED':
        return (
          <View style={[styles.statusBadge, styles.completedBadge]}>
            <Text style={[styles.statusText, styles.completedText]}>COMPLETED</Text>
          </View>
        );
      case 'CANCELLED':
        return (
          <View style={[styles.statusBadge, styles.cancelledBadge]}>
            <Text style={[styles.statusText, styles.cancelledText]}>CANCELLED</Text>
          </View>
        );
      default:
        return (
          <View style={[styles.statusBadge, styles.defaultBadge]}>
            <Text style={[styles.statusText, styles.defaultText]}>{appointment.status}</Text>
          </View>
        );
    }
  };

  return (
    <View style={styles.cardContainer}>
      {/* Top Doctor Row */}
      <View style={styles.topRow}>
        <Image
          source={{
            uri:
              appointment.doctor_photo ||
              'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&q=80&w=150',
          }}
          style={styles.doctorAvatar}
        />

        <View style={styles.infoBox}>
          <View style={styles.headerRow}>
            <Text style={styles.doctorName}>{appointment.doctor_name}</Text>
            {getStatusBadge()}
          </View>
          <Text style={styles.specialtyText}>{appointment.doctor_specialty}</Text>
          <Text style={styles.clinicText} numberOfLines={1}>
            {appointment.doctor_clinic}
          </Text>
        </View>
      </View>

      {/* Date & Time Row */}
      <View style={styles.scheduleRow}>
        <View style={styles.scheduleItem}>
          <Calendar size={14} color={COLORS.primary} />
          <Text style={styles.scheduleText}>{appointment.appointment_date}</Text>
        </View>

        <View style={styles.scheduleItem}>
          <Clock size={14} color={COLORS.primary} />
          <Text style={styles.scheduleText}>{appointment.appointment_time}</Text>
        </View>

        {appointment.consultation_fee ? (
          <Text style={styles.feeText}>₹{appointment.consultation_fee}</Text>
        ) : null}
      </View>

      {/* Visit Reason */}
      {appointment.visit_reason && (
        <View style={styles.reasonBox}>
          <Text style={styles.reasonLabel}>Reason: </Text>
          <Text style={styles.reasonText} numberOfLines={1}>
            {appointment.visit_reason}
          </Text>
        </View>
      )}

      {/* Cancel Button */}
      {onCancel && appointment.status !== 'CANCELLED' && appointment.status !== 'COMPLETED' && (
        <TouchableOpacity
          onPress={() => onCancel(appointment.id)}
          style={styles.cancelBtn}
          activeOpacity={0.7}
        >
          <XCircle size={14} color={COLORS.urgent} style={{ marginRight: 6 }} />
          <Text style={styles.cancelBtnText}>Cancel Consultation</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 16,
    marginBottom: 14,
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
    width: 52,
    height: 52,
    borderRadius: 15,
    backgroundColor: COLORS.background,
    marginRight: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  infoBox: {
    flex: 1,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  doctorName: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  specialtyText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
    marginTop: 1,
  },
  clinicText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    borderWidth: 1,
  },
  confirmedBadge: {
    backgroundColor: COLORS.normalLight,
    borderColor: '#BEE0D0',
  },
  completedBadge: {
    backgroundColor: COLORS.background,
    borderColor: COLORS.border,
  },
  cancelledBadge: {
    backgroundColor: COLORS.urgentLight,
    borderColor: '#F4C5BF',
  },
  defaultBadge: {
    backgroundColor: COLORS.primaryLight,
    borderColor: '#C0DCDD',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '800',
  },
  confirmedText: {
    color: COLORS.normal,
  },
  completedText: {
    color: COLORS.textSecondary,
  },
  cancelledText: {
    color: COLORS.urgent,
  },
  defaultText: {
    color: COLORS.primary,
  },
  scheduleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.background,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 9,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  scheduleItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  scheduleText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginLeft: 5,
  },
  feeText: {
    fontSize: 12,
    fontWeight: '800',
    color: COLORS.primaryDark,
  },
  reasonBox: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    paddingTop: 4,
  },
  reasonLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  reasonText: {
    fontSize: 11,
    color: COLORS.textPrimary,
    flex: 1,
  },
  cancelBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  cancelBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.urgent,
  },
});
