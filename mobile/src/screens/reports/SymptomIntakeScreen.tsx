import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  StyleSheet,
} from 'react-native';
import { Header } from '../../components/common/Header';
import { Button } from '../../components/common/Button';
import { DisclaimerCard } from '../../components/common/DisclaimerCard';
import { aiApi } from '../../api/aiApi';
import { useReportWizardStore } from '../../store/reportWizardStore';
import { COLORS } from '../../constants/colors';

const SYMPTOM_OPTIONS = [
  'Fatigue',
  'Dizziness',
  'Headache',
  'Pain / Discomfort',
  'Fever',
  'Nausea',
  'Shortness of breath',
  'Chest tightness',
  'Frequent urination',
  'Weight changes',
  'Other',
];

const DURATION_OPTIONS = ['Today', 'Few days', '1–2 weeks', 'More than 2 weeks'];

export const SymptomIntakeScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { reportId } = route.params || {};
  const [primaryConcern, setPrimaryConcern] = useState('');
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [duration, setDuration] = useState('Few days');
  const [severityScore, setSeverityScore] = useState(5);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const setActiveSymptomLogId = useReportWizardStore((state) => state.setActiveSymptomLogId);
  const setActiveRecommendation = useReportWizardStore((state) => state.setActiveRecommendation);

  const toggleSymptom = (sym: string) => {
    if (selectedSymptoms.includes(sym)) {
      setSelectedSymptoms((prev) => prev.filter((s) => s !== sym));
    } else {
      setSelectedSymptoms((prev) => [...prev, sym]);
    }
  };

  const getDurationDays = (dur: string) => {
    switch (dur) {
      case 'Today':
        return 1;
      case 'Few days':
        return 3;
      case '1–2 weeks':
        return 10;
      case 'More than 2 weeks':
        return 21;
      default:
        return 5;
    }
  };

  const handleSubmit = async () => {
    if (!primaryConcern.trim() && selectedSymptoms.length === 0) {
      Alert.alert(
        'Please Describe Your Concern',
        'Enter your main health concern or choose one or more symptoms below.'
      );
      return;
    }

    setSubmitting(true);
    try {
      const logRes = await aiApi.logSymptoms({
        report_id: reportId,
        primary_concern: primaryConcern.trim() || selectedSymptoms.join(', '),
        symptoms_list: selectedSymptoms,
        duration_days: getDurationDays(duration),
        severity_score: severityScore,
        body_region: 'General',
        additional_notes: notes.trim() || undefined,
      });

      setActiveSymptomLogId(logRes.id);

      const recResult = await aiApi.recommendSpecialty({
        report_id: reportId,
        symptom_log_id: logRes.id,
      });

      setActiveRecommendation(recResult);

      navigation.navigate('SpecialtyRecommendation', {
        recommendation: recResult,
        reportId,
      });
    } catch (err: any) {
      const errData = err.response?.data;
      const msg = errData?.error?.message || errData?.detail || 'Failed to analyze symptoms.';
      if (msg.includes('Consent required') || msg.includes('AI_PROCESSING')) {
        Alert.alert(
          'Consent Required',
          'AI Specialty Navigation requires your explicit consent to process reported health symptoms. Would you like to review and grant consent now?',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Manage Consents', onPress: () => navigation.navigate('Profile', { screen: 'PrivacyConsent' }) }
          ]
        );
      } else {
        Alert.alert('Analysis Error', msg);
      }
    } finally {
      setSubmitting(false);
    }

  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Symptom Check"
        subtitle="Help us guide you to the right specialist"
        onBack={() => navigation.goBack()}
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Main Concern Input */}
        <View style={styles.sectionBox}>
          <Text style={styles.sectionLabel}>What is your main concern?</Text>
          <View style={styles.inputWrapper}>
            <TextInput
              value={primaryConcern}
              onChangeText={setPrimaryConcern}
              placeholder="e.g. Feeling unusually tired, dizziness, or routine follow-up"
              placeholderTextColor={COLORS.textMuted}
              multiline
              numberOfLines={3}
              style={styles.textInput}
            />
          </View>
        </View>

        {/* Symptoms Chips */}
        <View style={styles.sectionBox}>
          <Text style={styles.sectionLabel}>Symptoms</Text>
          <View style={styles.chipsWrap}>
            {SYMPTOM_OPTIONS.map((sym) => {
              const isSelected = selectedSymptoms.includes(sym);
              return (
                <TouchableOpacity
                  key={sym}
                  onPress={() => toggleSymptom(sym)}
                  activeOpacity={0.7}
                  style={[styles.symptomChip, isSelected && styles.symptomChipActive]}
                >
                  <Text
                    style={[
                      styles.symptomChipText,
                      isSelected && styles.symptomChipTextActive,
                    ]}
                  >
                    {sym}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Duration Selection */}
        <View style={styles.sectionBox}>
          <Text style={styles.sectionLabel}>How long?</Text>
          <View style={styles.durationRow}>
            {DURATION_OPTIONS.map((dur) => {
              const isSelected = duration === dur;
              return (
                <TouchableOpacity
                  key={dur}
                  onPress={() => setDuration(dur)}
                  style={[styles.durationChip, isSelected && styles.durationChipActive]}
                  activeOpacity={0.7}
                >
                  <Text
                    style={[
                      styles.durationText,
                      isSelected && styles.durationTextActive,
                    ]}
                  >
                    {dur}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Severity Scale */}
        <View style={styles.sectionBox}>
          <View style={styles.severityHeader}>
            <Text style={styles.sectionLabel}>Severity</Text>
            <Text style={styles.severityVal}>
              {severityScore <= 3 ? 'Mild' : severityScore <= 7 ? 'Moderate' : 'Severe'} ({severityScore}/10)
            </Text>
          </View>

          <View style={styles.severityBar}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
              <TouchableOpacity
                key={num}
                onPress={() => setSeverityScore(num)}
                style={[
                  styles.severityStep,
                  severityScore === num && styles.severityStepActive,
                ]}
              >
                <Text
                  style={[
                    styles.severityStepText,
                    severityScore === num && styles.severityStepTextActive,
                  ]}
                >
                  {num}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Additional Notes */}
        <View style={styles.sectionBox}>
          <Text style={styles.sectionLabel}>Additional notes (Optional)</Text>
          <View style={styles.inputWrapper}>
            <TextInput
              value={notes}
              onChangeText={setNotes}
              placeholder="Any past medical history, medication, or family context..."
              placeholderTextColor={COLORS.textMuted}
              multiline
              numberOfLines={2}
              style={[styles.textInput, { height: 60 }]}
            />
          </View>
        </View>

        {/* CTA Button */}
        <Button
          title="Find Recommended Specialist"
          onPress={handleSubmit}
          loading={submitting}
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
  sectionBox: {
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  inputWrapper: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    borderRadius: 18,
    padding: 14,
    boxShadow: '0px 1px 4px rgba(38, 51, 52, 0.02)',
    elevation: 1,
  },
  textInput: {
    fontSize: 14,
    color: COLORS.textPrimary,
    minHeight: 70,
    textAlignVertical: 'top',
  },
  chipsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  symptomChip: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  symptomChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  symptomChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  symptomChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  durationRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  durationChip: {
    flex: 1,
    minWidth: '45%',
    paddingVertical: 11,
    paddingHorizontal: 10,
    alignItems: 'center',
    borderRadius: 14,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  durationChipActive: {
    backgroundColor: COLORS.primaryLight,
    borderColor: COLORS.primary,
  },
  durationText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  durationTextActive: {
    color: COLORS.primaryDark,
    fontWeight: '700',
  },
  severityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  severityVal: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
  },
  severityBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: COLORS.surface,
    padding: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
  },
  severityStep: {
    flex: 1,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
  },
  severityStepActive: {
    backgroundColor: COLORS.primary,
  },
  severityStepText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textSecondary,
  },
  severityStepTextActive: {
    color: '#ffffff',
  },
});
