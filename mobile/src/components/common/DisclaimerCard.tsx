import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ShieldCheck } from 'lucide-react-native';
import { COLORS } from '../../constants/colors';

export const DisclaimerCard: React.FC = () => {
  return (
    <View style={styles.cardContainer}>
      <View style={styles.iconBox}>
        <ShieldCheck size={18} color={COLORS.primary} />
      </View>
      <View style={styles.textBox}>
        <Text style={styles.titleText}>Clinical Guidance & Safety</Text>
        <Text style={styles.descText}>
          VitaLens provides AI-assisted explanations to help you understand your reports and find appropriate doctors. It is not a substitute for professional medical advice, diagnosis, or emergency care.
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.secondaryLight,
    borderWidth: 1,
    borderColor: '#D5E4DB',
    borderRadius: 18,
    padding: 14,
    marginVertical: 10,
  },
  iconBox: {
    marginRight: 12,
    marginTop: 1,
  },
  textBox: {
    flex: 1,
  },
  titleText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginBottom: 2,
  },
  descText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    lineHeight: 16,
  },
});
