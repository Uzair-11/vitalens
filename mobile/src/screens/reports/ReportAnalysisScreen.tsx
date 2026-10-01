import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import {
  MessageSquare,
  ArrowRight,
  BookOpen,
  AlertCircle,
  CheckCircle,
  Stethoscope,
  Info,
} from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { BiomarkerCard } from '../../components/reports/BiomarkerCard';
import { TerminologyModal } from '../../components/reports/TerminologyModal';
import { DisclaimerCard } from '../../components/common/DisclaimerCard';
import { Button } from '../../components/common/Button';
import { reportApi } from '../../api/reportApi';
import { MedicalReportDetail, Biomarker } from '../../types';
import { useReportWizardStore } from '../../store/reportWizardStore';
import { COLORS } from '../../constants/colors';

export const ReportAnalysisScreen: React.FC<{ route: any; navigation: any }> = ({
  route,
  navigation,
}) => {
  const { reportId } = route.params;
  const [report, setReport] = useState<MedicalReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [glossaryModalVisible, setGlossaryModalVisible] = useState(false);
  const [selectedTerm, setSelectedTerm] = useState<string | null>(null);
  const [selectedBio, setSelectedBio] = useState<Biomarker | null>(null);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const setActiveReport = useReportWizardStore((state) => state.setActiveReport);

  const loadReport = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const data = await reportApi.getReportDetail(reportId);
      setReport(data);
      setActiveReport(data);
    } catch (e: any) {
      console.warn('Error loading report detail:', e);
      setErrorMessage(e?.response?.data?.detail || 'This report could not be found or has been removed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [reportId]);

  const handleExplainTerm = (term: string) => {
    setSelectedTerm(term);
    const matched = report?.biomarkers.find(
      (b) => b.test_name.toLowerCase() === term.toLowerCase() || b.canonical_name?.toLowerCase() === term.toLowerCase()
    );
    setSelectedBio(matched || null);
    setGlossaryModalVisible(true);
  };

  const handleProceedToSymptoms = () => {
    navigation.navigate('SymptomIntake', { reportId });
  };

  const handleAskQuestion = () => {
    navigation.navigate('ReportQA', { reportId });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading report explanation...</Text>
      </SafeAreaView>
    );
  }

  if (!report) {
    return (
      <SafeAreaView style={styles.container}>
        <Header
          title="Report Unavailable"
          subtitle="Report not found"
          onBack={() => navigation.navigate('ReportsList')}
        />
        <View style={styles.errorContainer}>
          <AlertCircle size={52} color={COLORS.urgent} style={{ marginBottom: 16 }} />
          <Text style={styles.errorTitle}>Report Not Found</Text>
          <Text style={styles.errorSubtitle}>
            {errorMessage || 'This medical report could not be found. It may have been deleted or the database was reset.'}
          </Text>
          <TouchableOpacity
            onPress={() => navigation.navigate('ReportsList')}
            style={styles.backBtn}
            activeOpacity={0.85}
          >
            <Text style={styles.backBtnText}>Return to Reports</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const abnormalBiomarkers = report.biomarkers.filter((b) => b.flag !== 'NORMAL');
  const normalBiomarkers = report.biomarkers.filter((b) => b.flag === 'NORMAL');

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title={report.file_name}
        subtitle="AI-assisted report explanation"
        onBack={() => navigation.goBack()}
        rightElement={
          <TouchableOpacity
            onPress={() => {
              setSelectedTerm(null);
              setSelectedBio(null);
              setGlossaryModalVisible(true);
            }}
            style={styles.glossaryHeaderBtn}
            activeOpacity={0.8}
          >
            <BookOpen size={14} color={COLORS.primary} />
            <Text style={styles.glossaryHeaderBtnText}>Glossary</Text>
          </TouchableOpacity>
        }
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Overall Summary Overview Card */}
        <View style={styles.overviewCard}>
          <View style={styles.overviewHeader}>
            <Text style={styles.overviewTitle}>Report Overview</Text>
            <Text style={styles.overviewDate}>{report.report_date}</Text>
          </View>

          <Text style={styles.overviewBody}>
            {abnormalBiomarkers.length === 0
              ? 'All extracted results are within the standard reference ranges shown on your report.'
              : `Most results are within reference range, but ${abnormalBiomarkers.length} values need attention.`}
          </Text>

          {report.analysis?.plain_summary ? (
            <View style={styles.summaryBox}>
              <Text style={styles.summaryText}>{report.analysis.plain_summary}</Text>
            </View>
          ) : null}

          {/* Ratio Counters */}
          <View style={styles.statsRow}>
            <View style={[styles.statBox, styles.statBoxNormal]}>
              <CheckCircle size={15} color={COLORS.normal} style={{ marginRight: 6 }} />
              <Text style={styles.statNormalText}>
                {normalBiomarkers.length} Normal
              </Text>
            </View>

            {abnormalBiomarkers.length > 0 && (
              <View style={[styles.statBox, styles.statBoxAbnormal]}>
                <AlertCircle size={15} color={COLORS.urgent} style={{ marginRight: 6 }} />
                <Text style={styles.statAbnormalText}>
                  {abnormalBiomarkers.length} Attention
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Ask About Report CTA */}
        <TouchableOpacity
          onPress={handleAskQuestion}
          activeOpacity={0.85}
          style={styles.qaCard}
        >
          <View style={styles.qaIconCircle}>
            <MessageSquare size={18} color={COLORS.primary} />
          </View>
          <View style={{ flex: 1, marginRight: 8 }}>
            <Text style={styles.qaTitle}>Ask about your report</Text>
            <Text style={styles.qaSubtitle}>Get instant answers grounded in these test results</Text>
          </View>
          <ArrowRight size={16} color={COLORS.primary} />
        </TouchableOpacity>

        {/* Extracted Biomarkers Section */}
        <View style={styles.sectionHeaderBox}>
          <Text style={styles.sectionTitle}>Test Results & Ranges</Text>
          <Text style={styles.sectionSubtitle}>Tap any item to view explanation and gauge</Text>
        </View>

        {report.biomarkers.map((bio, index) => (
          <BiomarkerCard
            key={bio.id || bio.test_name}
            biomarker={bio}
            onExplainTerm={handleExplainTerm}
            initiallyExpanded={index === 0 && bio.flag !== 'NORMAL'}
          />
        ))}

        {/* "What Should I Do Next?" Bridge CTA */}
        <View style={styles.nextStepCard}>
          <View style={styles.nextStepHeader}>
            <View style={styles.nextStepIconBox}>
              <Stethoscope size={18} color={COLORS.primary} />
            </View>
            <Text style={styles.nextStepHeading}>What should I do next?</Text>
          </View>

          <Text style={styles.nextStepText}>
            Have a health concern? Tell us what you're experiencing to help identify an appropriate medical specialty.
          </Text>

          <TouchableOpacity
            onPress={handleProceedToSymptoms}
            style={styles.findSpecialistBtn}
            activeOpacity={0.85}
          >
            <Text style={styles.findSpecialistBtnText}>Find the Right Specialist</Text>
            <ArrowRight size={16} color="#ffffff" style={{ marginLeft: 6 }} />
          </TouchableOpacity>
        </View>

        <DisclaimerCard />
        <View style={{ height: 24 }} />
      </ScrollView>

      {/* Medical Terminology Modal */}
      <TerminologyModal
        visible={glossaryModalVisible}
        onClose={() => setGlossaryModalVisible(false)}
        glossary={report.analysis?.terminology_glossary || []}
        selectedTerm={selectedTerm}
        patientValue={selectedBio?.value_numeric ?? selectedBio?.value_text}
        referenceRange={
          selectedBio?.reference_min !== undefined && selectedBio?.reference_max !== undefined
            ? `${selectedBio.reference_min} – ${selectedBio.reference_max} ${selectedBio.unit || ''}`
            : selectedBio?.reference_text
        }
        clinicalNote={selectedBio?.clinical_interpretation}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 8,
  },
  glossaryHeaderBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primaryLight,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#C0DCDD',
  },
  glossaryHeaderBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginLeft: 4,
  },
  scrollArea: {
    padding: 20,
  },
  overviewCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
    marginBottom: 16,
  },
  overviewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  overviewTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  overviewDate: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  overviewBody: {
    fontSize: 13,
    color: COLORS.textPrimary,
    lineHeight: 18,
    fontWeight: '600',
  },
  summaryBox: {
    backgroundColor: COLORS.background,
    borderRadius: 14,
    padding: 14,
    marginTop: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  summaryText: {
    fontSize: 12,
    color: COLORS.textPrimary,
    lineHeight: 18,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 14,
  },
  statBox: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 12,
    borderWidth: 1,
  },
  statBoxNormal: {
    backgroundColor: COLORS.normalLight,
    borderColor: '#BEE0D0',
  },
  statNormalText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.normal,
  },
  statBoxAbnormal: {
    backgroundColor: COLORS.urgentLight,
    borderColor: '#F4C5BF',
  },
  statAbnormalText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.urgent,
  },
  qaCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: 18,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 20,
    boxShadow: '0px 1px 4px rgba(38, 51, 52, 0.02)',
    elevation: 1,
  },
  qaIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  qaTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  qaSubtitle: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  sectionHeaderBox: {
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textPrimary,
    letterSpacing: -0.2,
  },
  sectionSubtitle: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  nextStepCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 20,
    borderWidth: 1.5,
    borderColor: '#D5E4DB',
    marginTop: 10,
    marginBottom: 16,
  },
  nextStepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  nextStepIconBox: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  nextStepHeading: {
    fontSize: 15,
    fontWeight: '800',
    color: COLORS.primaryDark,
  },
  nextStepText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 18,
    marginBottom: 16,
  },
  findSpecialistBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 14,
    paddingVertical: 13,
    boxShadow: '0px 2px 4px rgba(18, 54, 45, 0.15)',
    elevation: 2,
  },
  findSpecialistBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffffff',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 8,
    textAlign: 'center',
  },
  errorSubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  backBtn: {
    marginTop: 24,
    backgroundColor: COLORS.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 14,
  },
  backBtnText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 14,
  },
});
