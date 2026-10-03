import React, { useEffect, useCallback } from 'react';
import * as SplashScreen from 'expo-splash-screen';
import { View, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList } from './types';
import { AuthNavigator } from './AuthNavigator';
import { AppTabNavigator } from './AppTabNavigator';
import { useAuthStore } from '../store/authStore';
import { COLORS } from '../constants/colors';

const Stack = createNativeStackNavigator<RootStackParamList>();

export const RootNavigator = () => {
  const token = useAuthStore((state) => state.token);
  const isLoading = useAuthStore((state) => state.isLoading);
  const loadSession = useAuthStore((state) => state.loadSession);

  useEffect(() => {
    let isMounted = true;
    const initSession = async () => {
      try {
        await loadSession();
      } catch (err) {
        console.warn('[RootNavigator] Session load failed:', err);
      } finally {
        if (isMounted) {
          // Immediately dismiss native splash screen once session is checked
          await SplashScreen.hideAsync().catch(() => {});
        }
      }
    };
    initSession();

    // Fast fallback timer: never leave splash screen stuck for more than 800ms
    const safetyTimer = setTimeout(() => {
      SplashScreen.hideAsync().catch(() => {});
    }, 800);

    return () => {
      isMounted = false;
      clearTimeout(safetyTimer);
    };
  }, [loadSession]);

  const onNavigationReady = useCallback(async () => {
    try {
      await SplashScreen.hideAsync();
    } catch (e) {
      // Ignore if already dismissed
    }
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, backgroundColor: '#ffffff', justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={COLORS.primary || '#0F5C5E'} />
      </View>
    );
  }

  return (
    <NavigationContainer onReady={onNavigationReady}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {token ? (
          <Stack.Screen name="App" component={AppTabNavigator} />
        ) : (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};
