import React from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { Check, Calendar, Clock, MapPin, Stethoscope } from 'lucide-react-native';
import { Button } from '../../components/common/Button';
import { Appointment } from '../../types';
import { COLORS } from '../../constants/colors';

export const BookingSuccessScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const appointment: Appointment = route.params?.appointment;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollCenter} showsVerticalScrollIndicator={false}>
        {/* Success Icon */}
        <View style={styles.iconCircle}>
          <Check size={36} color="#ffffff" strokeWidth={3.5} />
        </View>

        <Text style={styles.heading}>Appointment confirmed</Text>
        <Text style={styles.subheading}>
          Your consultation is scheduled and confirmed with the clinic.
        </Text>

        {/* Appointment Confirmation Card */}
        <View style={styles.ticketCard}>
          <View style={styles.ticketTop}>
            <View>
              <Text style={styles.doctorName}>
                {appointment?.doctor_name || 'Specialist Doctor'}
              </Text>
              <Text style={styles.doctorSpec}>
                {appointment?.doctor_specialty || 'General Medicine'}
              </Text>
            </View>
            <View style={styles.doctorIconBox}>
              <Stethoscope size={20} color={COLORS.primary} />
            </View>
          </View>

          {/* Schedule Info */}
          <View style={styles.scheduleRow}>
            <View style={styles.scheduleItem}>
              <Text style={styles.scheduleLabel}>Date</Text>
              <View style={styles.scheduleValRow}>
                <Calendar size={13} color={COLORS.primary} style={{ marginRight: 5 }} />
                <Text style={styles.scheduleVal}>{appointment?.appointment_date}</Text>
              </View>
            </View>

            <View style={styles.scheduleItem}>
              <Text style={styles.scheduleLabel}>Time Slot</Text>
              <View style={styles.scheduleValRow}>
                <Clock size={13} color={COLORS.primary} style={{ marginRight: 5 }} />
                <Text style={styles.scheduleVal}>{appointment?.appointment_time}</Text>
              </View>
            </View>
          </View>

          {/* Clinic Location */}
          <View style={styles.clinicRow}>
            <Text style={styles.scheduleLabel}>Clinic</Text>
            <View style={styles.clinicDetailsRow}>
              <MapPin size={14} color={COLORS.textSecondary} style={{ marginRight: 6, marginTop: 1 }} />
              <Text style={styles.clinicText}>
                {appointment?.doctor_clinic} · {appointment?.doctor_address}
              </Text>
            </View>
          </View>
        </View>

        {/* CTAs */}
        <Button
          title="View Appointment"
          onPress={() => navigation.navigate('AppointmentsTab')}
          size="lg"
          style={{ width: '100%', marginBottom: 10 }}
        />

        <Button
          title="Back to Home"
          onPress={() => navigation.navigate('HomeTab')}
          variant="outline"
          size="md"
          style={{ width: '100%' }}
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
  scrollCenter: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.normal,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    boxShadow: '0px 4px 8px rgba(22, 163, 74, 0.25)',
    elevation: 4,
  },
  heading: {
    fontSize: 22,
    fontWeight: '900',
    color: COLORS.textPrimary,
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  subheading: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
    maxWidth: 300,
  },
  ticketCard: {
    width: '100%',
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 4px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
    marginBottom: 24,
  },
  ticketTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  doctorName: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  doctorSpec: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
    marginTop: 2,
  },
  doctorIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scheduleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 14,
  },
  scheduleItem: {
    flex: 1,
  },
  scheduleLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  scheduleValRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  scheduleVal: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  clinicRow: {
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  clinicDetailsRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 2,
  },
  clinicText: {
    fontSize: 12,
    color: COLORS.textPrimary,
    flex: 1,
    lineHeight: 16,
  },
});
