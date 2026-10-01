import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { Search, Stethoscope, X } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { DoctorCard } from '../../components/doctors/DoctorCard';
import { doctorApi } from '../../api/doctorApi';
import { Doctor, Specialty } from '../../types';
import { COLORS } from '../../constants/colors';

export const DoctorListScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const initialSpecialtyId = route.params?.specialtyId;
  const initialSpecialtyName = route.params?.specialtyName;

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [selectedSpecialtyId, setSelectedSpecialtyId] = useState<string | null>(initialSpecialtyId || null);
  const [selectedSpecialtyName, setSelectedSpecialtyName] = useState<string | null>(initialSpecialtyName || null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSpecialties = async () => {
      try {
        const specs = await doctorApi.getSpecialties();
        setSpecialties(specs);
      } catch (e) {
        console.warn('Error fetching specialties:', e);
      }
    };
    fetchSpecialties();
  }, []);

  const fetchDoctors = async () => {
    setLoading(true);
    try {
      const data = await doctorApi.searchDoctors({
        specialty_id: selectedSpecialtyId || undefined,
        sort_by: 'rating_desc',
      });
      setDoctors(data);
    } catch (e) {
      console.warn('Error fetching doctors:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctors();
  }, [selectedSpecialtyId]);

  const filteredDoctors = doctors.filter(
    (d) =>
      d.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.clinic_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.specialty_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Find a Doctor"
        subtitle="Consult top verified medical specialists"
        showLogo
      />

      {/* Recommended Specialty Pill if arrived from recommendation */}
      {selectedSpecialtyName ? (
        <View style={styles.filterBanner}>
          <View style={styles.filterBadge}>
            <Text style={styles.filterBadgeLabel}>Recommended specialty: </Text>
            <Text style={styles.filterBadgeValue}>{selectedSpecialtyName}</Text>
            <TouchableOpacity
              onPress={() => {
                setSelectedSpecialtyId(null);
                setSelectedSpecialtyName(null);
              }}
              style={styles.clearFilterBtn}
            >
              <X size={14} color={COLORS.primaryDark} />
            </TouchableOpacity>
          </View>
        </View>
      ) : null}

      {/* Search Input Bar */}
      <View style={styles.searchBox}>
        <View style={styles.searchInner}>
          <Search size={18} color={COLORS.textSecondary} />
          <TextInput
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="Search doctors, specialty, clinic..."
            placeholderTextColor={COLORS.textMuted}
            style={styles.searchInput}
          />
        </View>
      </View>

      {/* Specialty Filter Chips */}
      <View style={styles.chipsContainer}>
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={[{ id: 'all', name: 'All Doctors' }, ...specialties]}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ paddingHorizontal: 20 }}
          renderItem={({ item }) => {
            const isSelected =
              (item.id === 'all' && !selectedSpecialtyId) || selectedSpecialtyId === item.id;
            return (
              <TouchableOpacity
                onPress={() => {
                  if (item.id === 'all') {
                    setSelectedSpecialtyId(null);
                    setSelectedSpecialtyName(null);
                  } else {
                    setSelectedSpecialtyId(item.id);
                    setSelectedSpecialtyName(item.name);
                  }
                }}
                style={[styles.specialtyChip, isSelected && styles.specialtyChipActive]}
                activeOpacity={0.7}
              >
                <Text
                  style={[
                    styles.specialtyChipText,
                    isSelected && styles.specialtyChipTextActive,
                  ]}
                >
                  {item.name}
                </Text>
              </TouchableOpacity>
            );
          }}
        />
      </View>

      {/* Doctor List */}
      {loading ? (
        <View style={styles.centerLoader}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          data={filteredDoctors}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listPadding}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => (
            <DoctorCard
              doctor={item}
              onPress={() => navigation.navigate('DoctorProfile', { doctorId: item.id })}
            />
          )}
          ListEmptyComponent={
            <View style={styles.emptyBox}>
              <Stethoscope size={36} color={COLORS.secondary} />
              <Text style={styles.emptyTitle}>No Doctors Found</Text>
              <Text style={styles.emptySubtitle}>
                Try selecting a different specialty or clearing your search filter.
              </Text>
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
  filterBanner: {
    paddingHorizontal: 20,
    paddingTop: 10,
    backgroundColor: COLORS.surface,
  },
  filterBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primaryLight,
    borderWidth: 1,
    borderColor: '#C0DCDD',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  filterBadgeLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  filterBadgeValue: {
    fontSize: 12,
    fontWeight: '800',
    color: COLORS.primaryDark,
  },
  clearFilterBtn: {
    marginLeft: 6,
    padding: 2,
  },
  searchBox: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: COLORS.surface,
  },
  searchInner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 12,
    height: 46,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 13,
    color: COLORS.textPrimary,
  },
  chipsContainer: {
    backgroundColor: COLORS.surface,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  specialtyChip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 12,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginRight: 8,
  },
  specialtyChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  specialtyChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  specialtyChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
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
  emptyTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginTop: 12,
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
});
