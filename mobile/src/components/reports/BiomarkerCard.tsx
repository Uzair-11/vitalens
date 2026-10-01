import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, LayoutAnimation, Platform } from 'react-native';
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle, Info } from 'lucide-react-native';
import { RangeBarGauge } from './RangeBarGauge';
import { Biomarker } from '../../types';
import { COLORS } from '../../constants/colors';

interface BiomarkerCardProps {
  biomarker: Biomarker;
  onExplainTerm?: (term: string) => void;
  initiallyExpanded?: boolean;
}

export const BiomarkerCard: React.FC<BiomarkerCardProps> = ({
  biomarker,
  onExplainTerm,
  initiallyExpanded = false,
}) => {
  const [expanded, setExpanded] = useState(initiallyExpanded);

  const flag = biomarker.flag?.toUpperCase() || 'NORMAL';
  const isHigh = flag === 'HIGH';
  const isLow = flag === 'LOW';
  const isCritical = flag === 'CRITICAL' || flag === 'ABNORMAL' || flag === 'URGENT';
  const isNormal = flag === 'NORMAL';

  const toggleExpand = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
  };

  const getStatusColor = () => {
    if (isNormal) return COLORS.normal;
    if (isLow || isHigh) return COLORS.attention;
    return COLORS.urgent;
  };

  const getStatusBg = () => {
    if (isNormal) return COLORS.normalLight;
    if (isLow || isHigh) return COLORS.attentionLight;
    return COLORS.urgentLight;
  };

  const getStatusBorder = () => {
    if (isNormal) return '#BEE0D0';
    if (isLow || isHigh) return '#F7E2B5';
    return '#F4C5BF';
  };

  const getStatusLabel = () => {
    if (isNormal) return 'NORMAL';
    if (isLow) return 'LOW';
    if (isHigh) return 'HIGH';
    if (isCritical) return 'ATTENTION NEEDED';
    return flag;
  };

  const getExplanation = () => {
    if (biomarker.clinical_interpretation) {
      return biomarker.clinical_interpretation;
    }
    if (isLow) {
      return `Your ${biomarker.test_name} result (${biomarker.value_numeric ?? biomarker.value_text} ${biomarker.unit || ''}) is below the reference range shown on your report (${biomarker.reference_min} – ${biomarker.reference_max} ${biomarker.unit || ''}).`;
    }
    if (isHigh || isCritical) {
      return `Your ${biomarker.test_name} result (${biomarker.value_numeric ?? biomarker.value_text} ${biomarker.unit || ''}) is above the reference range shown on your report (${biomarker.reference_min} – ${biomarker.reference_max} ${biomarker.unit || ''}).`;
    }
    return `Your ${biomarker.test_name} is within the normal healthy reference range (${biomarker.reference_min ?? ''} – ${biomarker.reference_max ?? ''} ${biomarker.unit || ''}).`;
  };

  return (
    <View style={styles.cardContainer}>
      <TouchableOpacity
        onPress={toggleExpand}
        activeOpacity={0.8}
        style={styles.mainTouchable}
      >
        <View style={styles.topRow}>
          <View style={styles.nameCategoryCol}>
            <Text style={styles.testNameText}>{biomarker.test_name}</Text>
            {biomarker.category ? (
              <Text style={styles.categoryText}>{biomarker.category}</Text>
            ) : null}
          </View>

          <View style={[styles.statusBadge, { backgroundColor: getStatusBg(), borderColor: getStatusBorder() }]}>
            {isNormal ? (
              <CheckCircle size={12} color={COLORS.normal} style={styles.badgeIcon} />
            ) : (
              <AlertCircle size={12} color={getStatusColor()} style={styles.badgeIcon} />
            )}
            <Text style={[styles.statusBadgeText, { color: getStatusColor() }]}>
              {getStatusLabel()}
            </Text>
          </View>
        </View>

        {/* Value Row */}
        <View style={styles.valueRow}>
          <View style={styles.valueGroup}>
            <Text style={styles.numericValue}>
              {biomarker.value_numeric !== null && biomarker.value_numeric !== undefined
                ? biomarker.value_numeric
                : biomarker.value_text}
            </Text>
            {biomarker.unit ? <Text style={styles.unitText}>{biomarker.unit}</Text> : null}
          </View>

          <View style={styles.expandRow}>
            <Text style={styles.refSummary}>
              Ref: {biomarker.reference_min ?? ''}{biomarker.reference_min !== undefined && biomarker.reference_max !== undefined ? ' – ' : ''}{biomarker.reference_max ?? biomarker.reference_text ?? 'Standard'}
            </Text>
            {expanded ? (
              <ChevronUp size={18} color={COLORS.textSecondary} style={{ marginLeft: 6 }} />
            ) : (
              <ChevronDown size={18} color={COLORS.textSecondary} style={{ marginLeft: 6 }} />
            )}
          </View>
        </View>
      </TouchableOpacity>

      {/* Expandable Explanation Section */}
      {expanded && (
        <View style={styles.expandedContent}>
          <View style={styles.divider} />

          {/* Visual Range Gauge */}
          {typeof biomarker.value_numeric === 'number' &&
          typeof biomarker.reference_min === 'number' &&
          typeof biomarker.reference_max === 'number' ? (
            <RangeBarGauge
              value={biomarker.value_numeric}
              min={biomarker.reference_min}
              max={biomarker.reference_max}
              unit={biomarker.unit || ''}
              flag={biomarker.flag}
            />
          ) : null}

          {/* Plain English Explanation */}
          <View style={styles.explanationBox}>
            <Text style={styles.explanationTitle}>What does this mean?</Text>
            <Text style={styles.explanationBody}>{getExplanation()}</Text>
          </View>

          {/* Learn More Action */}
          {onExplainTerm && (
            <TouchableOpacity
              onPress={() => onExplainTerm(biomarker.canonical_name || biomarker.test_name)}
              style={styles.learnMoreBtn}
              activeOpacity={0.7}
            >
              <Info size={14} color={COLORS.primary} style={{ marginRight: 6 }} />
              <Text style={styles.learnMoreText}>
                Learn about {biomarker.test_name}
              </Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 12,
    boxShadow: '0px 2px 6px rgba(38, 51, 52, 0.03)',
    elevation: 1,
    overflow: 'hidden',
  },
  mainTouchable: {
    padding: 16,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  nameCategoryCol: {
    flex: 1,
    marginRight: 10,
  },
  testNameText: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.textPrimary,
    letterSpacing: -0.1,
  },
  categoryText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 10,
    borderWidth: 1,
  },
  badgeIcon: {
    marginRight: 4,
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  valueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
  },
  valueGroup: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  numericValue: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  unitText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginLeft: 6,
  },
  expandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  refSummary: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  expandedContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.borderSubtle,
    marginBottom: 12,
  },
  explanationBox: {
    backgroundColor: COLORS.background,
    borderRadius: 14,
    padding: 12,
    marginTop: 6,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  explanationTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: 4,
  },
  explanationBody: {
    fontSize: 12,
    color: COLORS.textPrimary,
    lineHeight: 18,
  },
  learnMoreBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    alignSelf: 'flex-start',
    paddingVertical: 4,
  },
  learnMoreText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
  },
});
