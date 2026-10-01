import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Alert,
  StyleSheet,
} from 'react-native';
import { UploadCloud, Camera, FileText, CheckCircle2, ShieldCheck } from 'lucide-react-native';
import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from 'expo-image-picker';
import { Header } from '../../components/common/Header';
import { reportApi } from '../../api/reportApi';
import { Button } from '../../components/common/Button';
import { DisclaimerCard } from '../../components/common/DisclaimerCard';
import { COLORS } from '../../constants/colors';

export const UploadReportScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [selectedFile, setSelectedFile] = useState<{ uri: string; name: string; type: string } | null>(null);
  const [uploading, setUploading] = useState(false);

  const handlePickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedFile({
          uri: asset.uri,
          name: asset.name,
          type: asset.mimeType || 'application/pdf',
        });
      }
    } catch (e) {
      Alert.alert('File Picker Error', 'Unable to select the document.');
    }
  };

  const handlePickImage = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Needed', 'Photo gallery access is required to upload report images.');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality: 0.9,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedFile({
          uri: asset.uri,
          name: `medical_report_${Date.now()}.jpg`,
          type: 'image/jpeg',
        });
      }
    } catch (e) {
      Alert.alert('Gallery Error', 'Unable to load photo gallery.');
    }
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) {
      Alert.alert('No File Selected', 'Please choose a file or take a photo of your report.');
      return;
    }

    setUploading(true);
    try {
      console.log('📄 [UploadReportScreen] Initiating upload for file:', selectedFile.name, selectedFile.type);
      const uploadRes = await reportApi.uploadReport(
        selectedFile.uri,
        selectedFile.name,
        selectedFile.type
      );
      const reportId = uploadRes.report_id;
      console.log('🚀 [UploadReportScreen] Navigating to ProcessingReport with ID:', reportId);
      navigation.navigate('ProcessingReport', { reportId });
    } catch (err: any) {
      console.error('❌ [UploadReportScreen] Upload error:', err);
      const detailMsg = err.response?.data?.detail;
      const msg = typeof detailMsg === 'string' 
        ? detailMsg 
        : (err.message === 'Network Error' 
            ? 'Network Error: Cannot connect to the VitaLens backend server. Please verify your phone and computer are connected to the same Wi-Fi network.' 
            : (err.message || 'Upload failed. Please try again.'));
      Alert.alert('Upload Failed', msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Upload Medical Report"
        subtitle="We'll extract and analyze the content automatically"
        onBack={() => navigation.goBack()}
      />

      <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
        {/* Main Upload Box */}
        <View style={styles.uploadCard}>
          <View style={styles.uploadIconCircle}>
            <UploadCloud size={32} color={COLORS.primary} />
          </View>
          <Text style={styles.uploadCardTitle}>Upload your report</Text>
          <Text style={styles.uploadCardSpecs}>PDF, JPG or PNG · Up to 10 MB</Text>

          <TouchableOpacity
            onPress={handlePickDocument}
            style={styles.chooseFileBtn}
            activeOpacity={0.85}
          >
            <Text style={styles.chooseFileBtnText}>Choose File</Text>
          </TouchableOpacity>

          <Text style={styles.orText}>or</Text>

          <TouchableOpacity
            onPress={handlePickImage}
            style={styles.takePhotoBtn}
            activeOpacity={0.85}
          >
            <Camera size={16} color={COLORS.primaryDark} style={{ marginRight: 6 }} />
            <Text style={styles.takePhotoBtnText}>Take a Photo</Text>
          </TouchableOpacity>
        </View>

        {/* Selected File Feedback */}
        {selectedFile && (
          <View style={styles.fileSelectedBox}>
            <View style={styles.fileRow}>
              <CheckCircle2 size={18} color={COLORS.normal} style={{ marginRight: 8 }} />
              <Text style={styles.fileName} numberOfLines={1}>
                {selectedFile.name}
              </Text>
              <TouchableOpacity onPress={() => setSelectedFile(null)}>
                <Text style={styles.changeFileText}>Change</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* CTA Button */}
        <Button
          title="Begin AI Report Analysis"
          onPress={handleStartAnalysis}
          disabled={!selectedFile || uploading}
          loading={uploading}
          size="lg"
          style={{ marginBottom: 16 }}
        />

        {/* Privacy & Security Note */}
        <View style={styles.privacyCard}>
          <ShieldCheck size={18} color={COLORS.primary} style={{ marginRight: 10, marginTop: 1 }} />
          <Text style={styles.privacyText}>
            Your report contains sensitive health information. It is stored securely and is only accessible through your authenticated account.
          </Text>
        </View>

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
  uploadCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 24,
    padding: 28,
    borderWidth: 1.5,
    borderColor: '#D5E4DB',
    borderStyle: 'dashed',
    alignItems: 'center',
    marginBottom: 16,
  },
  uploadIconCircle: {
    width: 64,
    height: 64,
    borderRadius: 20,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  uploadCardTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  uploadCardSpecs: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 18,
  },
  chooseFileBtn: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 28,
    paddingVertical: 12,
    borderRadius: 14,
    boxShadow: '0px 2px 4px rgba(18, 54, 45, 0.15)',
    elevation: 2,
  },
  chooseFileBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  orText: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginVertical: 10,
    fontWeight: '600',
  },
  takePhotoBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 12,
  },
  takePhotoBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  fileSelectedBox: {
    backgroundColor: COLORS.normalLight,
    borderWidth: 1,
    borderColor: '#BEE0D0',
    borderRadius: 16,
    padding: 14,
    marginBottom: 16,
  },
  fileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  fileName: {
    flex: 1,
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginRight: 8,
  },
  changeFileText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textSecondary,
  },
  privacyCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 12,
  },
  privacyText: {
    flex: 1,
    fontSize: 11,
    color: COLORS.textSecondary,
    lineHeight: 16,
  },
});
