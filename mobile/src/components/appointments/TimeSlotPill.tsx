import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { Clock } from 'lucide-react-native';
import { COLORS } from '../../constants/colors';

interface TimeSlotPillProps {
  timeStr: string;
  isSelected: boolean;
  isBooked: boolean;
  onPress: () => void;
}

export const TimeSlotPill: React.FC<TimeSlotPillProps> = ({
  timeStr,
  isSelected,
  isBooked,
  onPress,
}) => {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isBooked}
      activeOpacity={0.8}
      style={[
        styles.pillContainer,
        isSelected && styles.selectedPill,
        isBooked && styles.bookedPill,
      ]}
    >
      <Clock
        size={13}
        color={isSelected ? '#ffffff' : isBooked ? COLORS.textMuted : COLORS.textSecondary}
        style={{ marginRight: 5 }}
      />
      <Text
        style={[
          styles.pillText,
          isSelected && styles.selectedText,
          isBooked && styles.bookedText,
        ]}
      >
        {timeStr.slice(0, 5)}
      </Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  pillContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
    marginRight: 8,
    marginBottom: 8,
  },
  selectedPill: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
    boxShadow: '0px 2px 4px rgba(18, 54, 45, 0.2)',
    elevation: 2,
  },
  bookedPill: {
    backgroundColor: COLORS.background,
    borderColor: COLORS.borderSubtle,
    opacity: 0.6,
  },
  pillText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  selectedText: {
    color: '#ffffff',
  },
  bookedText: {
    color: COLORS.textMuted,
    textDecorationLine: 'line-through',
  },
});
