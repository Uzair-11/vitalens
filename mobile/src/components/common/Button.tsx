import React from 'react';
import { TouchableOpacity, Text, ActivityIndicator, View, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/colors';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'coral' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  style?: any;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  style,
}) => {
  const getContainerStyle = () => {
    switch (variant) {
      case 'secondary':
        return styles.secondaryBtn;
      case 'coral':
        return styles.coralBtn;
      case 'outline':
        return styles.outlineBtn;
      case 'danger':
        return styles.dangerBtn;
      case 'ghost':
        return styles.ghostBtn;
      default:
        return styles.primaryBtn;
    }
  };

  const getTextStyle = () => {
    switch (variant) {
      case 'secondary':
        return styles.secondaryBtnText;
      case 'coral':
        return styles.coralBtnText;
      case 'outline':
        return styles.outlineBtnText;
      case 'danger':
        return styles.dangerBtnText;
      case 'ghost':
        return styles.ghostBtnText;
      default:
        return styles.primaryBtnText;
    }
  };

  const getSizeStyle = () => {
    switch (size) {
      case 'sm':
        return styles.smSize;
      case 'lg':
        return styles.lgSize;
      default:
        return styles.mdSize;
    }
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.85}
      style={[
        styles.baseBtn,
        getContainerStyle(),
        getSizeStyle(),
        (disabled || loading) && styles.disabledBtn,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variant === 'outline' || variant === 'ghost' ? COLORS.primary : '#ffffff'}
        />
      ) : (
        <View style={styles.contentRow}>
          {icon && <View style={styles.iconBox}>{icon}</View>}
          <Text style={[styles.baseText, getTextStyle()]}>{title}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  baseBtn: {
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  primaryBtn: {
    backgroundColor: COLORS.primary,
    boxShadow: '0px 2px 4px rgba(18, 54, 45, 0.15)',
    elevation: 2,
  },
  secondaryBtn: {
    backgroundColor: COLORS.secondary,
  },
  coralBtn: {
    backgroundColor: COLORS.accent,
    boxShadow: '0px 2px 4px rgba(59, 130, 246, 0.2)',
    elevation: 2,
  },
  outlineBtn: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },
  ghostBtn: {
    backgroundColor: 'transparent',
  },
  dangerBtn: {
    backgroundColor: COLORS.urgent,
  },
  disabledBtn: {
    opacity: 0.5,
  },
  smSize: {
    height: 38,
    paddingHorizontal: 14,
  },
  mdSize: {
    height: 50,
    paddingHorizontal: 20,
  },
  lgSize: {
    height: 56,
    paddingHorizontal: 24,
  },
  contentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBox: {
    marginRight: 8,
  },
  baseText: {
    fontWeight: '700',
    fontSize: 15,
    letterSpacing: 0.2,
  },
  primaryBtnText: {
    color: '#ffffff',
  },
  secondaryBtnText: {
    color: '#ffffff',
  },
  coralBtnText: {
    color: '#ffffff',
  },
  outlineBtnText: {
    color: COLORS.textPrimary,
  },
  ghostBtnText: {
    color: COLORS.primary,
  },
  dangerBtnText: {
    color: '#ffffff',
  },
});
