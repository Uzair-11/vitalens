import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/colors';

interface RangeBarGaugeProps {
  value: number;
  min?: number;
  max?: number;
  unit?: string;
  flag?: string;
}

export const RangeBarGauge: React.FC<RangeBarGaugeProps> = ({
  value,
  min = 0,
  max = 100,
  unit = '',
  flag = 'NORMAL',
}) => {
  const rangeSpan = Math.max(max - min, 1);
  const gaugeMin = Math.max(0, min - rangeSpan * 0.4);
  const gaugeMax = max + rangeSpan * 0.4;
  const totalSpan = gaugeMax - gaugeMin;

  const percent = Math.min(Math.max(((value - gaugeMin) / totalSpan) * 100, 4), 96);
  const normalStart = ((min - gaugeMin) / totalSpan) * 100;
  const normalWidth = ((max - min) / totalSpan) * 100;

  const isLow = flag === 'LOW';
  const isHigh = flag === 'HIGH';
  const isCritical = flag === 'CRITICAL' || flag === 'ABNORMAL' || flag === 'URGENT';

  const markerColor = isLow || isHigh ? COLORS.attention : isCritical ? COLORS.urgent : COLORS.normal;

  return (
    <View style={styles.gaugeContainer}>
      {/* 3-Band Horizontal Gauge Track */}
      <View style={styles.trackContainer}>
        <View style={styles.lowBand} />
        <View style={[styles.normalBand, { left: `${normalStart}%`, width: `${normalWidth}%` }]} />
        <View style={styles.highBand} />

        {/* Needle Marker Indicator */}
        <View
          style={[
            styles.needleMarker,
            {
              left: `${percent}%`,
              backgroundColor: markerColor,
            },
          ]}
        />
      </View>

      {/* Numerical Bounds Labels */}
      <View style={styles.labelsRow}>
        <Text style={styles.rangeLabel}>Min: {min} {unit}</Text>
        <Text style={[styles.currentLabel, { color: markerColor }]}>
          Observed: {value} {unit}
        </Text>
        <Text style={styles.rangeLabel}>Max: {max} {unit}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  gaugeContainer: {
    width: '100%',
    marginVertical: 10,
  },
  trackContainer: {
    height: 8,
    borderRadius: 4,
    backgroundColor: '#F7E6E4',
    position: 'relative',
    overflow: 'visible',
    flexDirection: 'row',
  },
  lowBand: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: '30%',
    backgroundColor: '#FDF0DA',
    borderTopLeftRadius: 4,
    borderBottomLeftRadius: 4,
  },
  normalBand: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    backgroundColor: '#D9ECE3',
  },
  highBand: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: '30%',
    backgroundColor: '#F7E6E4',
    borderTopRightRadius: 4,
    borderBottomRightRadius: 4,
  },
  needleMarker: {
    position: 'absolute',
    top: -5,
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 3,
    borderColor: '#ffffff',
    marginLeft: -9,
    boxShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)',
    elevation: 3,
  },
  labelsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
  },
  rangeLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
    fontWeight: '500',
  },
  currentLabel: {
    fontSize: 11,
    fontWeight: '700',
  },
});
