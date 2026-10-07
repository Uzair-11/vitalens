import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { Calendar as CalendarIcon, Clock, CheckCircle2, ShieldCheck } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { Button } from '../../components/common/Button';
import { TimeSlotPill } from '../../components/appointments/TimeSlotPill';
import { doctorApi } from '../../api/doctorApi';
import { appointmentApi } from '../../api/appointmentApi';
import { DoctorSlot } from '../../types';
import { useReportWizardStore } from '../../store/reportWizardStore';
import { COLORS } from '../../constants/colors';

export const SlotSelectionScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { doctorId } = route.params;
  const activeReport = useReportWizardStore((state) => state.activeReport);
  const selectedDoctor = useReportWizardStore((state) => state.selectedDoctor);

  const [availableSlots, setAvailableSlots] = useState<DoctorSlot[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedSlot, setSelectedSlot] = useState<DoctorSlot | null>(null);
  const [visitReason, setVisitReason] = useState('Follow-up on laboratory report');
  const [patientNotes, setPatientNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    const fetchSlots = async () => {
      try {
        const slots = await doctorApi.getDoctorAvailability(doctorId);
        setAvailableSlots(slots);
        if (slots.length > 0) {
          setSelectedDate(slots[0].available_date);
        }
      } catch (e) {
        console.warn('Error fetching availability:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchSlots();
  }, [doctorId]);

  const uniqueDates = Array.from(new Set(availableSlots.map((s) => s.available_date)));
  const slotsForDate = availableSlots.filter((s) => s.available_date === selectedDate);

  const morningSlots = slotsForDate.filter((s) => parseInt(s.start_time.split(':')[0], 10) < 12);
  const afternoonSlots = slotsForDate.filter((s) => parseInt(s.start_time.split(':')[0], 10) >= 12);

  const handleConfirmBooking = async () => {
    if (!selectedSlot) {
      Alert.alert('Select Time Slot', 'Please choose an available appointment time slot.');
      return;
    }

    setBooking(true);
    try {
      const appt = await appointmentApi.bookAppointment({
        doctor_id: doctorId,
        appointment_date: selectedSlot.available_date,
        appointment_time: selectedSlot.start_time,
        report_id: activeReport?.id,
        visit_reason: visitReason.trim() || undefined,
        patient_notes: patientNotes.trim() || undefined,
      });

      const enrichedAppointment: Appointment = {
        ...appt,
        doctor_name: appt.doctor_name || selectedDoctor?.full_name,
        doctor_specialty: appt.doctor_specialty || selectedDoctor?.specialty_name,
        doctor_clinic: appt.doctor_clinic || selectedDoctor?.clinic_name,
        doctor_address: appt.doctor_address || selectedDoctor?.address,
        doctor_photo: appt.doctor_photo || selectedDoctor?.profile_photo_url,
        consultation_fee: appt.consultation_fee ?? selectedDoctor?.consultation_fee,
      };

      navigation.replace('BookingSuccess', { appointment: enrichedAppointment });
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Booking failed. This slot might be taken.';
      Alert.alert('Booking Error', msg);
    } finally {
      setBooking(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Book a Slot"
        subtitle={selectedDoctor?.full_name || 'Select Consultation Slot'}
        onBack={() => navigation.goBack()}
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Date Selector */}
        <View style={styles.sectionBlock}>
          <Text style={styles.sectionHeading}>Consultation Date</Text>
          {loading ? (
            <ActivityIndicator size="small" color={COLORS.primary} style={{ marginVertical: 12 }} />
          ) : (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.dateScrollView}>
              {uniqueDates.map((d) => {
                const isSelected = selectedDate === d;
                return (
                  <TouchableOpacity
                    key={d}
                    onPress={() => {
                      setSelectedDate(d);
                      setSelectedSlot(null);
                    }}
                    style={[styles.dateChip, isSelected && styles.dateChipActive]}
                    activeOpacity={0.75}
                  >
                    <CalendarIcon size={14} color={isSelected ? '#ffffff' : COLORS.textSecondary} />
                    <Text style={[styles.dateText, isSelected && styles.dateTextActive]}>
                      {d}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          )}
        </View>

        {/* Time Slots */}
        <View style={styles.slotsCard}>
          <Text style={styles.slotsCardTitle}>Available Slots on {selectedDate}</Text>

          {/* Morning Slots */}
          <Text style={styles.slotGroupLabel}>Morning</Text>
          <View style={styles.slotsWrap}>
            {morningSlots.length > 0 ? (
              morningSlots.map((slot) => (
                <TimeSlotPill
                  key={slot.id}
                  timeStr={slot.start_time}
                  isSelected={selectedSlot?.id === slot.id}
                  isBooked={slot.is_booked}
                  onPress={() => setSelectedSlot(slot)}
                />
              ))
            ) : (
              <Text style={styles.noSlotsText}>No morning slots available</Text>
            )}
          </View>

          {/* Afternoon Slots */}
          <Text style={[styles.slotGroupLabel, { marginTop: 12 }]}>Afternoon</Text>
          <View style={styles.slotsWrap}>
            {afternoonSlots.length > 0 ? (
              afternoonSlots.map((slot) => (
                <TimeSlotPill
                  key={slot.id}
                  timeStr={slot.start_time}
                  isSelected={selectedSlot?.id === slot.id}
                  isBooked={slot.is_booked}
                  onPress={() => setSelectedSlot(slot)}
                />
              ))
            ) : (
              <Text style={styles.noSlotsText}>No afternoon slots available</Text>
            )}
          </View>
        </View>

        {/* Review Appointment Card */}
        <View style={styles.reviewCard}>
          <Text style={styles.reviewHeading}>Review appointment</Text>

          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Doctor</Text>
            <Text style={styles.reviewVal}>{selectedDoctor?.full_name || 'Specialist'}</Text>
          </View>

          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Specialty</Text>
            <Text style={styles.reviewVal}>{selectedDoctor?.specialty_name || 'Medicine'}</Text>
          </View>

          {selectedSlot ? (
            <View style={styles.reviewRow}>
              <Text style={styles.reviewLabel}>Time & Date</Text>
              <Text style={styles.reviewVal}>
                {selectedSlot.available_date} · {selectedSlot.start_time.slice(0, 5)}
              </Text>
            </View>
          ) : null}

          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Clinic</Text>
            <Text style={styles.reviewVal}>{selectedDoctor?.clinic_name}</Text>
          </View>

          <View style={styles.reviewRow}>
            <Text style={styles.reviewLabel}>Consultation</Text>
            <Text style={[styles.reviewVal, { color: COLORS.primaryDark, fontWeight: '800' }]}>
              ₹{selectedDoctor?.consultation_fee || '800'}
            </Text>
          </View>

          {activeReport && (
            <View style={styles.linkedReportBox}>
              <CheckCircle2 size={14} color={COLORS.normal} style={{ marginRight: 6 }} />
              <Text style={styles.linkedReportText}>
                Linked report: {activeReport.file_name}
              </Text>
            </View>
          )}

          <View style={{ marginTop: 12 }}>
            <Text style={styles.reasonInputLabel}>Reason for visit</Text>
            <TextInput
              value={visitReason}
              onChangeText={setVisitReason}
              placeholder="e.g. Fatigue, report review"
              placeholderTextColor={COLORS.textMuted}
              style={styles.reasonInput}
            />
          </View>
        </View>

        {/* Confirm Booking CTA */}
        <Button
          title="Confirm Appointment"
          onPress={handleConfirmBooking}
          loading={booking}
          disabled={!selectedSlot || booking}
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
  scrollArea: {
    padding: 20,
  },
  sectionBlock: {
    marginBottom: 16,
  },
  sectionHeading: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  dateScrollView: {
    flexDirection: 'row',
  },
  dateChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginRight: 8,
  },
  dateChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  dateText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginLeft: 6,
  },
  dateTextActive: {
    color: '#ffffff',
  },
  slotsCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 16,
  },
  slotsCardTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 10,
  },
  slotGroupLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textSecondary,
    marginBottom: 6,
  },
  slotsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  noSlotsText: {
    fontSize: 12,
    color: COLORS.textMuted,
    fontStyle: 'italic',
    paddingVertical: 4,
  },
  reviewCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 18,
  },
  reviewHeading: {
    fontSize: 15,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  reviewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  reviewLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  reviewVal: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  linkedReportBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.normalLight,
    padding: 10,
    borderRadius: 12,
    marginTop: 8,
  },
  linkedReportText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.normal,
  },
  reasonInputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  reasonInput: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 12,
    color: COLORS.textPrimary,
  },
});
