import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Platform } from 'react-native';
import { ChevronLeft } from 'lucide-react-native';
import { COLORS } from '../../constants/colors';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  rightElement?: React.ReactNode;
  /** Show the VitaLens brand icon beside the title (use on root-level screens with no back button) */
  showLogo?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onBack,
  rightElement,
  showLogo = false,
}) => {
  return (
    <View style={styles.headerContainer}>
      <View style={styles.leftRow}>
        {onBack && (
          <TouchableOpacity onPress={onBack} style={styles.backBtn} activeOpacity={0.7}>
            <ChevronLeft size={20} color={COLORS.textPrimary} />
          </TouchableOpacity>
        )}
        {showLogo && !onBack && (
          <Image
            source={require('../../../assets/images/vitalens-icon.png')}
            style={styles.brandIcon}
            resizeMode="contain"
          />
        )}
        <View style={styles.titleBox}>
          <Text style={styles.titleText}>{title}</Text>
          {subtitle && <Text style={styles.subtitleText}>{subtitle}</Text>}
        </View>
      </View>
      {rightElement && <View>{rightElement}</View>}
    </View>
  );
};

const styles = StyleSheet.create({
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'android' ? 18 : 16,
    paddingBottom: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
    zIndex: 10,
    elevation: 3,
  },
  leftRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  brandIcon: {
    width: 28,
    height: 28,
    marginRight: 10,
    borderRadius: 6,
  },
  titleBox: {
    flex: 1,
  },
  titleText: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.textPrimary,
    letterSpacing: -0.2,
  },
  subtitleText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
});
