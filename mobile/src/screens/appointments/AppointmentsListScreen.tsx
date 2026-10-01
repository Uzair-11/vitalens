import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Platform,
  StyleSheet,
} from 'react-native';
import { Calendar, Plus } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { AppointmentCard } from '../../components/appointments/AppointmentCard';
import { appointmentApi } from '../../api/appointmentApi';
import { Appointment } from '../../types';
import { COLORS } from '../../constants/colors';

export const AppointmentsListScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [activeTab, setActiveTab] = useState<'UPCOMING' | 'PAST'>('UPCOMING');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAppointments = async () => {
    try {
      const data = await appointmentApi.getAppointments();
      setAppointments(data);
    } catch (e) {
      console.warn('Error fetching appointments:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const handleCancel = async (appointmentId: string) => {
    const executeCancel = async () => {
      try {
        await appointmentApi.cancelAppointment(appointmentId, 'Cancelled by patient');
        setAppointments((prev) =>
          prev.map((a) => (a.id === appointmentId ? { ...a, status: 'CANCELLED' } : a))
        );
        if (Platform.OS === 'web') {
          window.alert('Consultation has been cancelled.');
        } else {
          Alert.alert('Consultation Cancelled', 'Your appointment has been cancelled.');
        }
      } catch (e: any) {
        const msg = e.response?.data?.detail || 'Failed to cancel appointment.';
        if (Platform.OS === 'web') {
          window.alert(msg);
        } else {
          Alert.alert('Cancellation Error', msg);
        }
      }
    };

    if (Platform.OS === 'web') {
      if (window.confirm('Are you sure you want to cancel this scheduled consultation?')) {
        await executeCancel();
      }
    } else {
      Alert.alert(
        'Cancel Appointment',
        'Are you sure you want to cancel this scheduled consultation?',
        [
          { text: 'Keep Appointment', style: 'cancel' },
          {
            text: 'Cancel Consultation',
            style: 'destructive',
            onPress: executeCancel,
          },
        ]
      );
    }
  };

  const filteredAppointments = appointments.filter((a) => {
    if (activeTab === 'UPCOMING') return a.status === 'CONFIRMED' || a.status === 'RESCHEDULED';
    return a.status === 'COMPLETED' || a.status === 'CANCELLED';
  });

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="My Appointments"
        subtitle="Manage your upcoming and past consultations"
        showLogo
        rightElement={
          <TouchableOpacity
            onPress={() => navigation.navigate('DoctorsTab', { screen: 'DoctorList' })}
            style={styles.bookBtn}
            activeOpacity={0.8}
          >
            <Plus size={16} color="#ffffff" style={{ marginRight: 4 }} />
            <Text style={styles.bookBtnText}>Book</Text>
          </TouchableOpacity>
        }
      />

      {/* Segmented Control Tabs */}
      <View style={styles.segmentContainer}>
        <TouchableOpacity
          onPress={() => setActiveTab('UPCOMING')}
          style={[styles.segmentBtn, activeTab === 'UPCOMING' && styles.segmentBtnActive]}
          activeOpacity={0.7}
        >
          <Text
            style={[styles.segmentText, activeTab === 'UPCOMING' && styles.segmentTextActive]}
          >
            Upcoming
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setActiveTab('PAST')}
          style={[styles.segmentBtn, activeTab === 'PAST' && styles.segmentBtnActive]}
          activeOpacity={0.7}
        >
          <Text style={[styles.segmentText, activeTab === 'PAST' && styles.segmentTextActive]}>
            Past
          </Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.centerLoader}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          data={filteredAppointments}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listPadding}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              tintColor={COLORS.primary}
              colors={[COLORS.primary]}
              onRefresh={() => {
                setRefreshing(true);
                fetchAppointments();
              }}
            />
          }
          renderItem={({ item }) => (
            <AppointmentCard
              appointment={item}
              onCancel={
                item.status !== 'CANCELLED' && item.status !== 'COMPLETED'
                  ? handleCancel
                  : undefined
              }
            />
          )}
          ListEmptyComponent={
            <View style={styles.emptyBox}>
              <View style={styles.emptyIconCircle}>
                <Calendar size={32} color={COLORS.secondary} />
              </View>
              <Text style={styles.emptyTitle}>
                No {activeTab === 'UPCOMING' ? 'upcoming' : 'past'} appointments
              </Text>
              <Text style={styles.emptySubtitle}>
                {activeTab === 'UPCOMING'
                  ? 'Find and connect with recommended doctors when you need specialist guidance.'
                  : 'You have no previous appointment history stored.'}
              </Text>
              {activeTab === 'UPCOMING' && (
                <TouchableOpacity
                  onPress={() => navigation.navigate('DoctorsTab', { screen: 'DoctorList' })}
                  style={styles.findDocBtn}
                  activeOpacity={0.85}
                >
                  <Text style={styles.findDocBtnText}>Find a Doctor</Text>
                </TouchableOpacity>
              )}
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  bookBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  bookBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  segmentContainer: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    padding: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
    gap: 8,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 9,
    alignItems: 'center',
    borderRadius: 12,
    backgroundColor: COLORS.background,
  },
  segmentBtnActive: {
    backgroundColor: COLORS.primary,
  },
  segmentText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textSecondary,
  },
  segmentTextActive: {
    color: '#ffffff',
  },
  centerLoader: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listPadding: {
    padding: 20,
    flexGrow: 1,
  },
  emptyBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
    paddingHorizontal: 20,
  },
  emptyIconCircle: {
    width: 64,
    height: 64,
    borderRadius: 20,
    backgroundColor: COLORS.secondaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 18,
  },
  findDocBtn: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 22,
    paddingVertical: 11,
    borderRadius: 14,
  },
  findDocBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
});
