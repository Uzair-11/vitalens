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
import { FileText, Plus, ArrowRight, Trash2, GitCompare, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react-native';
import { reportApi } from '../../api/reportApi';
import { MedicalReportSummary } from '../../types';
import { Header } from '../../components/common/Header';
import { COLORS } from '../../constants/colors';

const CATEGORIES = ['All', 'Blood', 'Thyroid', 'Lipid', 'Other'];

export const ReportsListScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [reports, setReports] = useState<MedicalReportSummary[]>([]);
  const [selectedFilter, setSelectedFilter] = useState('All');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchReports = async () => {
    try {
      const data = await reportApi.getAllReports();
      setReports(data);
    } catch (e) {
      console.warn('Error fetching reports:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDelete = async (reportId: string, fileName: string) => {
    const doDelete = async () => {
      try {
        await reportApi.deleteReport(reportId);
        setReports((prev) => prev.filter((r) => r.id !== reportId));
      } catch (e) {
        if (Platform.OS === 'web') {
          window.alert('Failed to delete report.');
        } else {
          Alert.alert('Error', 'Failed to delete report.');
        }
      }
    };

    if (Platform.OS === 'web') {
      if (window.confirm(`Are you sure you want to remove "${fileName}"?`)) {
        await doDelete();
      }
    } else {
      Alert.alert(
        'Delete Report',
        `Are you sure you want to remove "${fileName}"?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Delete',
            style: 'destructive',
            onPress: doDelete,
          },
        ]
      );
    }
  };

  const filteredReports = reports.filter((r) => {
    if (selectedFilter === 'All') return true;
    const repType = (r.report_type || '').toLowerCase();
    const fileName = (r.file_name || '').toLowerCase();
    return repType.includes(selectedFilter.toLowerCase()) || fileName.includes(selectedFilter.toLowerCase());
  });

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="My Reports"
        subtitle="Manage and analyze your diagnostic tests"
        showLogo
        rightElement={
          <TouchableOpacity
            onPress={() => navigation.navigate('UploadReport')}
            style={styles.addBtn}
            activeOpacity={0.8}
          >
            <Plus size={16} color="#ffffff" style={{ marginRight: 4 }} />
            <Text style={styles.addBtnText}>Upload</Text>
          </TouchableOpacity>
        }
      />

      {/* Filter Chips Row */}
      <View style={styles.filterRow}>
        {CATEGORIES.map((cat) => (
          <TouchableOpacity
            key={cat}
            onPress={() => setSelectedFilter(cat)}
            style={[styles.filterChip, selectedFilter === cat && styles.filterChipActive]}
            activeOpacity={0.7}
          >
            <Text
              style={[
                styles.filterChipText,
                selectedFilter === cat && styles.filterChipTextActive,
              ]}
            >
              {cat}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Trends & Comparison Quick Nav */}
      <View style={styles.utilityBar}>
        <TouchableOpacity
          onPress={() => navigation.navigate('BiomarkerTrends')}
          style={styles.utilityItem}
          activeOpacity={0.8}
        >
          <TrendingUp size={14} color={COLORS.primary} style={{ marginRight: 6 }} />
          <Text style={styles.utilityText}>Biomarker Trends</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => navigation.navigate('ReportComparison')}
          style={[styles.utilityItem, { marginLeft: 8 }]}
          activeOpacity={0.8}
        >
          <GitCompare size={14} color={COLORS.primary} style={{ marginRight: 6 }} />
          <Text style={styles.utilityText}>Compare Reports</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loaderCenter}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          data={filteredReports}
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
                fetchReports();
              }}
            />
          }
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => navigation.navigate('ReportAnalysis', { reportId: item.id })}
              activeOpacity={0.85}
              style={styles.reportCard}
            >
              <View style={styles.reportCardTop}>
                <View style={styles.iconCircle}>
                  <FileText size={20} color={COLORS.primary} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.reportName} numberOfLines={1}>
                    {item.file_name}
                  </Text>
                  <Text style={styles.reportDate}>{item.report_date}</Text>
                </View>

                {item.abnormal_count > 0 ? (
                  <View style={styles.abnormalBadge}>
                    <AlertCircle size={12} color={COLORS.urgent} style={{ marginRight: 4 }} />
                    <Text style={styles.abnormalBadgeText}>
                      {item.abnormal_count} need attention
                    </Text>
                  </View>
                ) : (
                  <View style={styles.normalBadge}>
                    <CheckCircle size={12} color={COLORS.normal} style={{ marginRight: 4 }} />
                    <Text style={styles.normalBadgeText}>Within range</Text>
                  </View>
                )}
              </View>

              <View style={styles.reportCardBottom}>
                <TouchableOpacity
                  onPress={() => handleDelete(item.id, item.file_name)}
                  style={styles.deleteAction}
                  activeOpacity={0.7}
                >
                  <Trash2 size={13} color={COLORS.textMuted} />
                  <Text style={styles.deleteActionText}>Delete</Text>
                </TouchableOpacity>

                <View style={styles.viewAction}>
                  <Text style={styles.viewActionText}>View Analysis</Text>
                  <ArrowRight size={14} color={COLORS.primary} />
                </View>
              </View>
            </TouchableOpacity>
          )}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View style={styles.emptyIconCircle}>
                <FileText size={32} color={COLORS.secondary} />
              </View>
              <Text style={styles.emptyTitle}>No reports yet</Text>
              <Text style={styles.emptySubtitle}>
                Upload your first medical report to start understanding your results.
              </Text>
              <TouchableOpacity
                onPress={() => navigation.navigate('UploadReport')}
                style={styles.emptyUploadBtn}
                activeOpacity={0.85}
              >
                <Text style={styles.emptyUploadBtnText}>Upload Report</Text>
              </TouchableOpacity>
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
  addBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  addBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  filterChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  filterChipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  utilityBar: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  utilityItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    paddingVertical: 9,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
  },
  utilityText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  loaderCenter: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listPadding: {
    padding: 20,
    flexGrow: 1,
  },
  reportCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
  },
  reportCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  reportName: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  reportDate: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  abnormalBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.urgentLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#F4C5BF',
  },
  abnormalBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.urgent,
  },
  normalBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.normalLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#BEE0D0',
  },
  normalBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.normal,
  },
  reportCardBottom: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  deleteAction: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 8,
    backgroundColor: COLORS.background,
  },
  deleteActionText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginLeft: 4,
  },
  viewAction: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewActionText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
    marginRight: 4,
  },
  emptyContainer: {
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
  emptyUploadBtn: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 20,
    paddingVertical: 11,
    borderRadius: 14,
  },
  emptyUploadBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
  },
});
