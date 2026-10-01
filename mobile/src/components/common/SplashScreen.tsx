import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import { COLORS } from '../../constants/colors';

const { width } = Dimensions.get('window');

export const SplashScreen: React.FC = () => {
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.8)).current;
  const textOpacity = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const dotOpacity1 = useRef(new Animated.Value(0.3)).current;
  const dotOpacity2 = useRef(new Animated.Value(0.3)).current;
  const dotOpacity3 = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const useNative = Platform.OS !== 'web';

    // Logo fade + scale in
    Animated.parallel([
      Animated.timing(logoOpacity, {
        toValue: 1,
        duration: 600,
        useNativeDriver: useNative,
      }),
      Animated.spring(logoScale, {
        toValue: 1,
        tension: 60,
        friction: 8,
        useNativeDriver: useNative,
      }),
    ]).start(() => {
      // Brand name fades in after logo
      Animated.timing(textOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: useNative,
      }).start(() => {
        // Tagline fades in last
        Animated.timing(taglineOpacity, {
          toValue: 1,
          duration: 400,
          useNativeDriver: useNative,
        }).start();
      });
    });

    // Loading dots animation
    const animateDots = () => {
      Animated.sequence([
        Animated.timing(dotOpacity1, { toValue: 1, duration: 300, useNativeDriver: useNative }),
        Animated.timing(dotOpacity2, { toValue: 1, duration: 300, useNativeDriver: useNative }),
        Animated.timing(dotOpacity3, { toValue: 1, duration: 300, useNativeDriver: useNative }),
        Animated.parallel([
          Animated.timing(dotOpacity1, { toValue: 0.3, duration: 300, useNativeDriver: useNative }),
          Animated.timing(dotOpacity2, { toValue: 0.3, duration: 300, useNativeDriver: useNative }),
          Animated.timing(dotOpacity3, { toValue: 0.3, duration: 300, useNativeDriver: useNative }),
        ]),
      ]).start(() => animateDots());
    };
    animateDots();
  }, []);

  return (
    <View style={styles.container}>
      {/* Logo */}
      <Animated.View
        style={[
          styles.logoWrapper,
          { opacity: logoOpacity, transform: [{ scale: logoScale }] },
        ]}
      >
        <Image
          source={require('../../../assets/images/vitalens-logo.png')}
          style={styles.logo}
          resizeMode="contain"
        />
      </Animated.View>

      {/* Brand Name */}
      <Animated.Text style={[styles.brandName, { opacity: textOpacity }]}>
        VitaLens
      </Animated.Text>

      {/* Tagline */}
      <Animated.Text style={[styles.tagline, { opacity: taglineOpacity }]}>
        Understand your health,{'\n'}one report at a time.
      </Animated.Text>

      {/* Loading dots */}
      <View style={styles.dotsRow}>
        <Animated.View style={[styles.dot, { opacity: dotOpacity1 }]} />
        <Animated.View style={[styles.dot, { opacity: dotOpacity2 }]} />
        <Animated.View style={[styles.dot, { opacity: dotOpacity3 }]} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F5C5E',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  logoWrapper: {
    marginBottom: 20,
    boxShadow: '0px 8px 16px rgba(0, 0, 0, 0.25)',
    elevation: 10,
  },
  logo: {
    width: width * 0.45,
    height: width * 0.45,
  },
  brandName: {
    fontSize: 36,
    fontWeight: '900',
    color: '#ffffff',
    letterSpacing: -1,
    marginBottom: 10,
  },
  tagline: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    lineHeight: 22,
    fontWeight: '400',
    letterSpacing: 0.2,
    marginBottom: 60,
  },
  dotsRow: {
    flexDirection: 'row',
    gap: 8,
    position: 'absolute',
    bottom: 60,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ffffff',
  },
});
