import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, ActivityIndicator, Alert, StyleSheet } from 'react-native';
import { Check, Dot, Circle } from 'lucide-react-native';
import { reportApi } from '../../api/reportApi';
import { useReportWizardStore } from '../../store/reportWizardStore';
import { COLORS } from '../../constants/colors';

const JOURNEY_STEPS = [
  { id: 1, label: 'Reading document' },
  { id: 2, label: 'Extracting test results' },
  { id: 3, label: 'Checking reference ranges' },
  { id: 4, label: 'Preparing explanation' },
  { id: 5, label: 'Preparing health guidance' },
];

export const ProcessingReportScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { reportId } = route.params;
  const [currentStep, setCurrentStep] = useState(1);
  const setActiveReport = useReportWizardStore((state) => state.setActiveReport);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    interval = setInterval(() => {
      setCurrentStep((prev) => (prev < 5 ? prev + 1 : prev));
    }, 700);

    const executeAnalysis = async () => {
      try {
        const reportDetail = await reportApi.analyzeReport(reportId);
        setActiveReport(reportDetail);

        setTimeout(() => {
          clearInterval(interval);
          navigation.replace('ReportAnalysis', { reportId });
        }, 3600);
      } catch (err: any) {
        clearInterval(interval);

        // Resilient check: Did the backend finish processing despite a network/timeout blip?
        try {
          const finishedReport = await reportApi.getReportDetail(reportId);
          if (finishedReport && finishedReport.status === 'COMPLETED') {
            setActiveReport(finishedReport);
            navigation.replace('ReportAnalysis', { reportId });
            return;
          }
        } catch {
          // Ignore secondary check errors and proceed to standard error alert
        }

        const errData = err.response?.data;
        const msg = errData?.error?.message || errData?.detail || 'Analysis could not be completed.';
        if (msg.includes('Consent required') || msg.includes('REPORT_ANALYSIS')) {
          Alert.alert(
            'Consent Required',
            'AI Report Analysis requires your explicit consent to extract and evaluate biomarkers. Would you like to review and grant consent now?',
            [
              { text: 'Cancel', style: 'cancel', onPress: () => navigation.goBack() },
              { text: 'Manage Consents', onPress: () => navigation.navigate('Profile', { screen: 'PrivacyConsent' }) }
            ]
          );
        } else {
          Alert.alert('Analysis Failed', msg, [
            { text: 'Go Back', onPress: () => navigation.goBack() },
          ]);
        }
      }

    };

    executeAnalysis();

    return () => clearInterval(interval);
  }, [reportId]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.centerContent}>
        {/* Animated Icon Indicator */}
        <View style={styles.spinnerCircle}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>

        <Text style={styles.heading}>Analyzing your report</Text>
        <Text style={styles.subheading}>
          Extracting biomarkers and assessing reference ranges
        </Text>

        {/* 5-Step Visual Processing Journey */}
        <View style={styles.journeyCard}>
          {JOURNEY_STEPS.map((step) => {
            const isDone = currentStep > step.id;
            const isCurrent = currentStep === step.id;

            return (
              <View key={step.id} style={styles.stepRow}>
                <View
                  style={[
                    styles.stepBullet,
                    isDone
                      ? styles.bulletDone
                      : isCurrent
                      ? styles.bulletCurrent
                      : styles.bulletPending,
                  ]}
                >
                  {isDone ? (
                    <Check size={12} color="#ffffff" strokeWidth={3} />
                  ) : isCurrent ? (
                    <View style={styles.currentDot} />
                  ) : null}
                </View>

                <Text
                  style={[
                    styles.stepLabel,
                    isDone
                      ? styles.labelDone
                      : isCurrent
                      ? styles.labelCurrent
                      : styles.labelPending,
                  ]}
                >
                  {step.label}
                </Text>
              </View>
            );
          })}
        </View>

        <Text style={styles.footerNote}>This may take a few moments.</Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  centerContent: {
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
  },
  spinnerCircle: {
    width: 72,
    height: 72,
    borderRadius: 24,
    backgroundColor: COLORS.primaryLight,
    borderWidth: 1,
    borderColor: '#C0DCDD',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  heading: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.textPrimary,
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  subheading: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 26,
  },
  journeyCard: {
    width: '100%',
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 22,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 4px 8px rgba(38, 51, 52, 0.04)',
    elevation: 2,
    marginBottom: 20,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 9,
  },
  stepBullet: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  bulletDone: {
    backgroundColor: COLORS.normal,
  },
  bulletCurrent: {
    backgroundColor: COLORS.primary,
  },
  bulletPending: {
    backgroundColor: COLORS.background,
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },
  currentDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ffffff',
  },
  stepLabel: {
    fontSize: 13,
    flex: 1,
  },
  labelDone: {
    color: COLORS.textPrimary,
    fontWeight: '600',
  },
  labelCurrent: {
    color: COLORS.primaryDark,
    fontWeight: '800',
  },
  labelPending: {
    color: COLORS.textMuted,
    fontWeight: '500',
  },
  footerNote: {
    fontSize: 12,
    color: COLORS.textSecondary,
    fontStyle: 'italic',
  },
});
