import React from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Stethoscope, Sparkles, ShieldAlert, ArrowRight, CheckCircle2 } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { Button } from '../../components/common/Button';
import { DisclaimerCard } from '../../components/common/DisclaimerCard';
import { SpecialtyRecommendationResult } from '../../types';
import { useReportWizardStore } from '../../store/reportWizardStore';
import { COLORS } from '../../constants/colors';

export const SpecialtyRecommendationScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const recommendation: SpecialtyRecommendationResult = route.params?.recommendation;
  const activeRecommendation = useReportWizardStore((state) => state.activeRecommendation);
  const rec = recommendation || activeRecommendation;

  const handleBrowseDoctors = () => {
    navigation.navigate('DoctorsTab', {
      screen: 'DoctorList',
      params: {
        specialtyId: rec?.recommended_specialty_id,
        specialtyName: rec?.recommended_specialty_name,
      },
    });
  };

  if (!rec) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyCenter}>
          <Text style={styles.emptyTitle}>No Recommendation Active</Text>
          <Button title="Go to Reports" onPress={() => navigation.navigate('ReportsList')} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Specialist Recommendation"
        subtitle="Suggested guidance based on your findings"
        onBack={() => navigation.goBack()}
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Urgent/Emergency Alert if flagged */}
        {rec.is_emergency_flagged && (
          <View style={styles.emergencyCard}>
            <View style={styles.emergencyHeader}>
              <ShieldAlert size={22} color="#ffffff" style={{ marginRight: 8 }} />
              <Text style={styles.emergencyTitle}>URGENT MEDICAL ATTENTION</Text>
            </View>
            <Text style={styles.emergencyBody}>
              {rec.emergency_message ||
                'Some of the information provided may require immediate clinical evaluation. Please contact emergency services or seek urgent care.'}
            </Text>
          </View>
        )}

        {/* Specialty Recommendation Card */}
        <View style={styles.recommendationCard}>
          <View style={styles.cardTopRow}>
            <View style={styles.iconCircle}>
              <Stethoscope size={26} color={COLORS.primary} />
            </View>
            <View style={styles.aiTag}>
              <Sparkles size={12} color={COLORS.primary} style={{ marginRight: 4 }} />
              <Text style={styles.aiTagText}>Suggested Specialist</Text>
            </View>
          </View>

          <Text style={styles.specialtyName}>{rec.recommended_specialty_name}</Text>
          <Text style={styles.specialtyDescription}>
            Based on your reported symptoms and report findings, this specialty may be a relevant consultation option. This is a suggestion to help guide your next step, not a diagnosis.
          </Text>

          {/* Transparent "Why this suggestion?" reasoning */}
          <View style={styles.rationaleBox}>
            <Text style={styles.rationaleHeading}>Why this suggestion?</Text>

            {rec.abnormal_biomarkers_considered && rec.abnormal_biomarkers_considered.length > 0 ? (
              <View style={styles.reasonItem}>
                <Text style={styles.bulletDot}>•</Text>
                <Text style={styles.reasonText}>
                  <Text style={styles.boldSpan}>Your report shows: </Text>
                  {rec.abnormal_biomarkers_considered.join(', ')}
                </Text>
              </View>
            ) : null}

            {rec.symptoms_considered && rec.symptoms_considered.length > 0 ? (
              <View style={styles.reasonItem}>
                <Text style={styles.bulletDot}>•</Text>
                <Text style={styles.reasonText}>
                  <Text style={styles.boldSpan}>You reported: </Text>
                  {rec.symptoms_considered.join(', ')}
                </Text>
              </View>
            ) : null}

            <Text style={styles.rationaleDetailText}>{rec.rationale}</Text>
          </View>
        </View>

        {/* Primary CTA */}
        <Button
          title={`Find ${rec.recommended_specialty_name} Doctors`}
          onPress={handleBrowseDoctors}
          icon={<ArrowRight size={18} color="#ffffff" />}
          size="lg"
          style={{ marginBottom: 14 }}
        />

        <DisclaimerCard />
        <View style={{ height: 24 }} />
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
  emptyCenter: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 12,
  },
  emergencyCard: {
    backgroundColor: COLORS.urgent,
    borderRadius: 22,
    padding: 18,
    marginBottom: 16,
  },
  emergencyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  emergencyTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#ffffff',
    letterSpacing: 0.3,
  },
  emergencyBody: {
    fontSize: 12,
    color: '#FDF0EE',
    lineHeight: 18,
  },
  recommendationCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 22,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 4px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
    marginBottom: 18,
  },
  cardTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  iconCircle: {
    width: 52,
    height: 52,
    borderRadius: 16,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  aiTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.secondaryLight,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D5E4DB',
  },
  aiTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  specialtyName: {
    fontSize: 24,
    fontWeight: '900',
    color: COLORS.textPrimary,
    letterSpacing: -0.3,
    marginBottom: 6,
  },
  specialtyDescription: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 19,
    marginBottom: 16,
  },
  rationaleBox: {
    backgroundColor: COLORS.background,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  rationaleHeading: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 10,
  },
  reasonItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  bulletDot: {
    fontSize: 14,
    fontWeight: '900',
    color: COLORS.primary,
    marginRight: 6,
    lineHeight: 17,
  },
  reasonText: {
    fontSize: 12,
    color: COLORS.textPrimary,
    flex: 1,
    lineHeight: 17,
  },
  boldSpan: {
    fontWeight: '700',
  },
  rationaleDetailText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 18,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
});
