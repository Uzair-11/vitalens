import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from 'react-native';
import { ArrowRight, TrendingDown, TrendingUp, Minus, GitCompare } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { DisclaimerCard } from '../../components/common/DisclaimerCard';
import { Button } from '../../components/common/Button';
import { reportApi } from '../../api/reportApi';
import { historyApi } from '../../api/historyApi';
import { MedicalReportSummary, ReportComparisonData } from '../../types';
import { COLORS } from '../../constants/colors';

export const ReportComparisonScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [reports, setReports] = useState<MedicalReportSummary[]>([]);
  const [selectedReport1, setSelectedReport1] = useState<string | null>(null);
  const [selectedReport2, setSelectedReport2] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<ReportComparisonData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const data = await reportApi.getAllReports();
        setReports(data);
        if (data.length >= 2) {
          setSelectedReport1(data[1].id);
          setSelectedReport2(data[0].id);
        } else if (data.length === 1) {
          setSelectedReport1(data[0].id);
          setSelectedReport2(data[0].id);
        }
      } catch (e) {
        console.warn('Error fetching reports:', e);
      }
    };
    fetchReports();
  }, []);

  const handleCompare = async () => {
    if (!selectedReport1 || !selectedReport2) {
      Alert.alert('Selection Needed', 'Please select two reports to compare.');
      return;
    }
    setLoading(true);
    try {
      const result = await historyApi.compareReports(selectedReport1, selectedReport2);
      setComparisonData(result);
    } catch (e) {
      Alert.alert('Comparison Error', 'Unable to compare selected reports.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'IMPROVED':
        return (
          <View style={[styles.statusBadge, styles.statusImproved]}>
            <TrendingDown size={11} color={COLORS.normal} />
            <Text style={styles.statusImprovedText}>IMPROVED</Text>
          </View>
        );
      case 'WORSENED':
        return (
          <View style={[styles.statusBadge, styles.statusWorsened]}>
            <TrendingUp size={11} color={COLORS.urgent} />
            <Text style={styles.statusWorsenedText}>WORSENED</Text>
          </View>
        );
      default:
        return (
          <View style={[styles.statusBadge, styles.statusStable]}>
            <Minus size={11} color={COLORS.textSecondary} />
            <Text style={styles.statusStableText}>STABLE</Text>
          </View>
        );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Report Comparison"
        subtitle="Side-by-side longitudinal delta analysis"
        onBack={() => navigation.goBack()}
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Selector Card */}
        <View style={styles.selectorCard}>
          <Text style={styles.selectorHeading}>Select Reports to Compare</Text>

          {reports.length >= 2 ? (
            <>
              <View style={styles.reportSelectGroup}>
                <Text style={styles.selectLabel}>Baseline (Earlier Report):</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsScroll}>
                  {reports.map((r) => (
                    <TouchableOpacity
                      key={r.id}
                      onPress={() => setSelectedReport1(r.id)}
                      style={[
                        styles.reportPill,
                        selectedReport1 === r.id && styles.reportPillActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.reportPillText,
                          selectedReport1 === r.id && styles.reportPillTextActive,
                        ]}
                      >
                        {r.report_date}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              <View style={styles.reportSelectGroup}>
                <Text style={styles.selectLabel}>Current (Follow-Up Report):</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsScroll}>
                  {reports.map((r) => (
                    <TouchableOpacity
                      key={r.id}
                      onPress={() => setSelectedReport2(r.id)}
                      style={[
                        styles.reportPill,
                        selectedReport2 === r.id && styles.reportPillActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.reportPillText,
                          selectedReport2 === r.id && styles.reportPillTextActive,
                        ]}
                      >
                        {r.report_date}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              <Button
                title="Generate Comparative Delta"
                onPress={handleCompare}
                loading={loading}
                style={{ marginTop: 8 }}
              />
            </>
          ) : (
            <Text style={styles.notEnoughText}>
              Please upload at least two medical reports to unlock side-by-side comparative analysis.
            </Text>
          )}
        </View>

        {/* Comparison Results */}
        {comparisonData && (
          <View style={styles.resultsCard}>
            <View style={styles.resultsHeader}>
              <Text style={styles.resultsTitle}>Biomarker Delta Table</Text>
              <Text style={styles.resultsSubtitle}>
                {comparisonData.report_1_date} vs {comparisonData.report_2_date}
              </Text>
            </View>

            {comparisonData.items.map((item, idx) => (
              <View key={idx} style={styles.comparisonRow}>
                <View style={styles.rowTop}>
                  <Text style={styles.testName}>{item.test_name}</Text>
                  {getStatusBadge(item.status_change)}
                </View>

                <View style={styles.valuesComparison}>
                  <View>
                    <Text style={styles.valLabel}>Previous</Text>
                    <Text style={styles.valNumber}>
                      {item.report_1_value ?? 'N/A'} {item.unit}
                    </Text>
                  </View>

                  <ArrowRight size={14} color={COLORS.textSecondary} />

                  <View>
                    <Text style={styles.valLabel}>Current</Text>
                    <Text style={styles.valNumber}>
                      {item.report_2_value ?? 'N/A'} {item.unit}
                    </Text>
                  </View>

                  {item.delta !== null && item.delta !== undefined && (
                    <Text
                      style={[
                        styles.deltaNumber,
                        {
                          color:
                            item.delta > 0
                              ? COLORS.urgent
                              : item.delta < 0
                              ? COLORS.normal
                              : COLORS.textSecondary,
                        },
                      ]}
                    >
                      {item.delta > 0 ? `+${item.delta}` : item.delta}
                    </Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        )}

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
  selectorCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 16,
  },
  selectorHeading: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 14,
  },
  reportSelectGroup: {
    marginBottom: 12,
  },
  selectLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.textSecondary,
    marginBottom: 6,
  },
  pillsScroll: {
    flexDirection: 'row',
  },
  reportPill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginRight: 8,
  },
  reportPillActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  reportPillText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  reportPillTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  notEnoughText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
  resultsCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 16,
  },
  resultsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
    marginBottom: 12,
  },
  resultsTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  resultsSubtitle: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  comparisonRow: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  rowTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  testName: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  valuesComparison: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.background,
    borderRadius: 12,
    padding: 10,
  },
  valLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  valNumber: {
    fontSize: 12,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginTop: 2,
  },
  deltaNumber: {
    fontSize: 13,
    fontWeight: '900',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  statusImproved: {
    backgroundColor: COLORS.normalLight,
  },
  statusImprovedText: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.normal,
    marginLeft: 3,
  },
  statusWorsened: {
    backgroundColor: COLORS.urgentLight,
  },
  statusWorsenedText: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.urgent,
    marginLeft: 3,
  },
  statusStable: {
    backgroundColor: COLORS.background,
  },
  statusStableText: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.textSecondary,
    marginLeft: 3,
  },
});
