import React, { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  StyleSheet,
} from 'react-native';
import Svg, { Polyline, Circle, Line } from 'react-native-svg';
import { Calendar, AlertCircle } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { DisclaimerCard } from '../../components/common/DisclaimerCard';
import { historyApi } from '../../api/historyApi';
import { BiomarkerTrendSeries } from '../../types';
import { COLORS } from '../../constants/colors';

const TRACKED_TESTS = ['Glucose', 'Cholesterol', 'Hemoglobin', 'Creatinine', 'TSH'];

export const BiomarkerTrendsScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [trends, setTrends] = useState<BiomarkerTrendSeries[]>([]);
  const [selectedTest, setSelectedTest] = useState('Glucose');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrends = async () => {
      try {
        const data = await historyApi.getTrends(TRACKED_TESTS);
        setTrends(data);
      } catch (e) {
        console.warn('Error loading trends:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchTrends();
  }, []);

  const activeSeries =
    trends.find((t) => t.canonical_name.toLowerCase().includes(selectedTest.toLowerCase())) ||
    trends[0];
  const points = activeSeries?.data_points || [];

  const chartWidth = Dimensions.get('window').width - 40;
  const chartHeight = 180;
  const paddingX = 40;
  const paddingY = 30;

  const minVal = points.length > 0 ? Math.min(...points.map((p) => p.value)) * 0.85 : 0;
  const maxVal = points.length > 0 ? Math.max(...points.map((p) => p.value)) * 1.15 : 100;
  const valRange = maxVal - minVal || 1;

  const coordinates = points.map((p, idx) => {
    const x = paddingX + (idx * (chartWidth - paddingX * 2)) / Math.max(1, points.length - 1);
    const y =
      chartHeight - paddingY - ((p.value - minVal) / valRange) * (chartHeight - paddingY * 2);
    return { x, y, ...p };
  });

  const polylinePoints = coordinates.map((c) => `${c.x},${c.y}`).join(' ');

  const latestPt = points.length > 0 ? points[points.length - 1] : null;
  const prevPt = points.length > 1 ? points[points.length - 2] : null;
  const delta = latestPt && prevPt ? (latestPt.value - prevPt.value).toFixed(1) : null;

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Your Health Trends"
        subtitle="Track biomarker variations over time"
        onBack={() => navigation.goBack()}
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Test Selector Chips */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipsScroll}>
          {TRACKED_TESTS.map((test) => {
            const isSelected = selectedTest === test;
            return (
              <TouchableOpacity
                key={test}
                onPress={() => setSelectedTest(test)}
                style={[styles.testChip, isSelected && styles.testChipActive]}
                activeOpacity={0.75}
              >
                <Text
                  style={[styles.testChipText, isSelected && styles.testChipTextActive]}
                >
                  {test}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {loading ? (
          <View style={styles.loaderCenter}>
            <ActivityIndicator size="large" color={COLORS.primary} />
          </View>
        ) : points.length > 0 ? (
          <>
            {/* Chart Card */}
            <View style={styles.chartCard}>
              <View style={styles.chartHeader}>
                <View>
                  <Text style={styles.categoryLabel}>{activeSeries?.category || 'Biomarker'}</Text>
                  <Text style={styles.seriesName}>{activeSeries?.canonical_name}</Text>
                </View>
                {latestPt && (
                  <View style={styles.latestValueBadge}>
                    <Text style={styles.latestValueText}>
                      {latestPt.value} {latestPt.unit}
                    </Text>
                  </View>
                )}
              </View>

              {/* Custom SVG Line Chart */}
              <View style={styles.svgWrapper}>
                <Svg width={chartWidth} height={chartHeight}>
                  <Line
                    x1={paddingX}
                    y1={paddingY}
                    x2={chartWidth - paddingX}
                    y2={paddingY}
                    stroke={COLORS.borderSubtle}
                    strokeWidth="1"
                  />
                  <Line
                    x1={paddingX}
                    y1={chartHeight - paddingY}
                    x2={chartWidth - paddingX}
                    y2={chartHeight - paddingY}
                    stroke={COLORS.borderSubtle}
                    strokeWidth="1"
                  />

                  <Polyline
                    points={polylinePoints}
                    fill="none"
                    stroke={COLORS.primary}
                    strokeWidth="3"
                  />

                  {coordinates.map((c, i) => (
                    <Circle
                      key={i}
                      cx={c.x}
                      cy={c.y}
                      r="5"
                      fill={
                        c.flag === 'HIGH' || c.flag === 'LOW' ? COLORS.attention : COLORS.primary
                      }
                      stroke="#ffffff"
                      strokeWidth="2"
                    />
                  ))}
                </Svg>
              </View>

              {/* X-Axis Dates */}
              <View style={styles.xAxisRow}>
                {points.map((p, idx) => (
                  <Text key={idx} style={styles.xAxisDate}>
                    {p.date}
                  </Text>
                ))}
              </View>

              {/* Delta Summary */}
              {latestPt && prevPt && (
                <View style={styles.deltaBox}>
                  <View style={styles.deltaCol}>
                    <Text style={styles.deltaLabel}>Latest result</Text>
                    <Text style={styles.deltaVal}>
                      {latestPt.value} {latestPt.unit}
                    </Text>
                  </View>

                  <View style={styles.deltaCol}>
                    <Text style={styles.deltaLabel}>Previous</Text>
                    <Text style={styles.deltaVal}>
                      {prevPt.value} {prevPt.unit}
                    </Text>
                  </View>

                  <View style={styles.deltaCol}>
                    <Text style={styles.deltaLabel}>Change</Text>
                    <Text
                      style={[
                        styles.deltaVal,
                        {
                          color:
                            parseFloat(delta || '0') > 0
                              ? COLORS.urgent
                              : parseFloat(delta || '0') < 0
                              ? COLORS.normal
                              : COLORS.textPrimary,
                        },
                      ]}
                    >
                      {parseFloat(delta || '0') > 0 ? `+${delta}` : delta}
                    </Text>
                  </View>
                </View>
              )}
            </View>

            {/* Historical Readings Table */}
            <View style={styles.historyCard}>
              <Text style={styles.historyHeading}>Historical Readings</Text>
              {points.map((pt, idx) => (
                <View key={idx} style={styles.historyRow}>
                  <View style={styles.historyDateRow}>
                    <Calendar size={13} color={COLORS.textSecondary} />
                    <Text style={styles.historyDateText}>{pt.date}</Text>
                  </View>
                  <View style={styles.historyValRow}>
                    <Text style={styles.historyValText}>
                      {pt.value} {pt.unit}
                    </Text>
                    <View
                      style={[
                        styles.historyStatusBadge,
                        pt.flag === 'NORMAL' ? styles.statusNormal : styles.statusAttention,
                      ]}
                    >
                      <Text
                        style={[
                          styles.historyStatusText,
                          pt.flag === 'NORMAL'
                            ? styles.statusNormalText
                            : styles.statusAttentionText,
                        ]}
                      >
                        {pt.flag}
                      </Text>
                    </View>
                  </View>
                </View>
              ))}
            </View>
          </>
        ) : (
          <View style={styles.emptyCard}>
            <AlertCircle size={32} color={COLORS.secondary} />
            <Text style={styles.emptyTitle}>Not enough data yet</Text>
            <Text style={styles.emptySubtitle}>
              Upload another report to start tracking your biomarkers over time.
            </Text>
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
  chipsScroll: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  testChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginRight: 8,
  },
  testChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  testChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  testChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  loaderCenter: {
    paddingVertical: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 16,
  },
  chartHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  categoryLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  seriesName: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  latestValueBadge: {
    backgroundColor: COLORS.primaryLight,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  latestValueText: {
    fontSize: 12,
    fontWeight: '800',
    color: COLORS.primaryDark,
  },
  svgWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 4,
  },
  xAxisRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  xAxisDate: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  deltaBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: COLORS.background,
    borderRadius: 14,
    padding: 12,
    marginTop: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  deltaCol: {
    alignItems: 'center',
    flex: 1,
  },
  deltaLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  deltaVal: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginTop: 2,
  },
  historyCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 16,
  },
  historyHeading: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 10,
  },
  historyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  historyDateRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  historyDateText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginLeft: 6,
  },
  historyValRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  historyValText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginRight: 8,
  },
  historyStatusBadge: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
  },
  statusNormal: {
    backgroundColor: COLORS.normalLight,
  },
  statusAttention: {
    backgroundColor: COLORS.attentionLight,
  },
  historyStatusText: {
    fontSize: 10,
    fontWeight: '700',
  },
  statusNormalText: {
    color: COLORS.normal,
  },
  statusAttentionText: {
    color: COLORS.attention,
  },
  emptyCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 30,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginTop: 8,
  },
  emptySubtitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
    marginTop: 4,
  },
});
