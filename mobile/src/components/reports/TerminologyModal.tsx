import React from 'react';
import { View, Text, Modal, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { X, BookOpen, Sparkles } from 'lucide-react-native';
import { GlossaryItem } from '../../types';
import { COLORS } from '../../constants/colors';

interface TerminologyModalProps {
  visible: boolean;
  onClose: () => void;
  glossary: GlossaryItem[];
  selectedTerm?: string | null;
  patientValue?: string | number | null;
  referenceRange?: string | null;
  clinicalNote?: string | null;
}

export const TerminologyModal: React.FC<TerminologyModalProps> = ({
  visible,
  onClose,
  glossary,
  selectedTerm,
  patientValue,
  referenceRange,
  clinicalNote,
}) => {
  const displayedItems = selectedTerm
    ? glossary.filter(
        (g) =>
          g.term.toLowerCase().includes(selectedTerm.toLowerCase()) ||
          selectedTerm.toLowerCase().includes(g.term.toLowerCase())
      )
    : glossary;

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.bottomSheet}>
          {/* Header */}
          <View style={styles.sheetHeader}>
            <View style={styles.headerTitleRow}>
              <View style={styles.iconBox}>
                <BookOpen size={18} color={COLORS.primary} />
              </View>
              <View>
                <Text style={styles.sheetTitle}>Medical Terminology</Text>
                <Text style={styles.sheetSubtitle}>Plain-English clinical definitions</Text>
              </View>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn} activeOpacity={0.7}>
              <X size={18} color={COLORS.textSecondary} />
            </TouchableOpacity>
          </View>

          {/* Body Content */}
          <ScrollView style={styles.scrollArea} showsVerticalScrollIndicator={false}>
            {selectedTerm && (
              <View style={styles.termHeroCard}>
                <View style={styles.termTagRow}>
                  <Text style={styles.termTagText}>Selected Biomarker</Text>
                </View>
                <Text style={styles.termHeroName}>{selectedTerm}</Text>

                {patientValue !== undefined && patientValue !== null && (
                  <View style={styles.metaRow}>
                    <View style={styles.metaBox}>
                      <Text style={styles.metaLabel}>In your report</Text>
                      <Text style={styles.metaVal}>{patientValue}</Text>
                    </View>
                    {referenceRange ? (
                      <View style={styles.metaBox}>
                        <Text style={styles.metaLabel}>Reference range</Text>
                        <Text style={styles.metaVal}>{referenceRange}</Text>
                      </View>
                    ) : null}
                  </View>
                )}

                {clinicalNote ? (
                  <Text style={styles.clinicalNoteText}>{clinicalNote}</Text>
                ) : null}
              </View>
            )}

            {/* Glossary Definitions */}
            {displayedItems.length > 0 ? (
              displayedItems.map((item, index) => (
                <View key={index} style={styles.definitionCard}>
                  <Text style={styles.defTerm}>{item.term}</Text>
                  <Text style={styles.defBody}>{item.definition}</Text>
                </View>
              ))
            ) : (
              <View style={styles.definitionCard}>
                <Text style={styles.defTerm}>{selectedTerm || 'Biomarker'}</Text>
                <Text style={styles.defBody}>
                  A standard diagnostic measurement assessed in laboratory blood panels to track organ health and bodily function.
                </Text>
              </View>
            )}

            <View style={styles.aiGroundedBadge}>
              <Sparkles size={14} color={COLORS.primary} style={{ marginRight: 6 }} />
              <Text style={styles.aiGroundedText}>
                Grounded in standard medical laboratory reference terminology.
              </Text>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(38, 51, 52, 0.45)',
    justifyContent: 'flex-end',
  },
  bottomSheet: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 22,
    maxHeight: '80%',
    boxShadow: '0px -4px 10px rgba(0, 0, 0, 0.1)',
    elevation: 8,
  },
  sheetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.borderSubtle,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: COLORS.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  sheetTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  sheetSubtitle: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollArea: {
    marginTop: 14,
  },
  termHeroCard: {
    backgroundColor: COLORS.background,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 14,
  },
  termTagRow: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginBottom: 6,
  },
  termTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.primary,
    textTransform: 'uppercase',
  },
  termHeroName: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 10,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
  },
  metaBox: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 10,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
  },
  metaLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  metaVal: {
    fontSize: 13,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginTop: 2,
  },
  clinicalNoteText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 17,
    marginTop: 6,
  },
  definitionCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    marginBottom: 10,
  },
  defTerm: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.primaryDark,
    marginBottom: 4,
  },
  defBody: {
    fontSize: 12,
    color: COLORS.textPrimary,
    lineHeight: 18,
  },
  aiGroundedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.secondaryLight,
    padding: 12,
    borderRadius: 14,
    marginTop: 6,
    marginBottom: 16,
  },
  aiGroundedText: {
    fontSize: 11,
    color: COLORS.primaryDark,
    flex: 1,
    lineHeight: 16,
  },
});
