import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { Send, Bot } from 'lucide-react-native';
import { Header } from '../../components/common/Header';
import { aiApi } from '../../api/aiApi';
import { COLORS } from '../../constants/colors';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  citations?: string[];
  disclaimer?: string;
}

const SUGGESTED_PROMPTS = [
  'What is MCV?',
  'Why is this value highlighted?',
  'What does this test measure?',
  'Which values are outside the reported reference range?',
];

export const ReportQAScreen: React.FC<{ route: any; navigation: any }> = ({ route, navigation }) => {
  const { reportId } = route.params;
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: 'Hello! I can explain the tests, biomarker ranges, and clinical details found in your uploaded medical report.',
      citations: ['Report Document'],
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (questionText?: string) => {
    const q = (questionText || inputText).trim();
    if (!q) return;

    const userMsg: Message = {
      id: `user_${Date.now()}`,
      sender: 'user',
      text: q,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!questionText) setInputText('');
    setLoading(true);

    try {
      const res = await aiApi.askReportQuestion(reportId, q);
      const aiMsg: Message = {
        id: `ai_${Date.now()}`,
        sender: 'ai',
        text: res.answer,
        citations: res.citations,
        disclaimer: res.disclaimer,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e) {
      const errorMsg: Message = {
        id: `ai_${Date.now()}`,
        sender: 'ai',
        text: 'I could not process your question at this moment. Please verify your connection and try again.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        title="Ask About Your Report"
        subtitle="Answers are based on information from this report"
        onBack={() => navigation.goBack()}
      />

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView style={styles.messagesScroll} showsVerticalScrollIndicator={false}>
          {/* Suggested Questions */}
          <View style={styles.suggestedBox}>
            <Text style={styles.suggestedHeading}>Suggested questions</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.suggestedRow}>
              {SUGGESTED_PROMPTS.map((prompt, idx) => (
                <TouchableOpacity
                  key={idx}
                  onPress={() => handleSend(prompt)}
                  disabled={loading}
                  style={styles.promptChip}
                  activeOpacity={0.75}
                >
                  <Text style={styles.promptChipText}>{prompt}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Message Bubbles */}
          {messages.map((msg) => (
            <View
              key={msg.id}
              style={[
                styles.messageRow,
                msg.sender === 'user' ? styles.userMessageRow : styles.aiMessageRow,
              ]}
            >
              {msg.sender === 'ai' && (
                <View style={styles.aiAvatar}>
                  <Bot size={16} color="#ffffff" />
                </View>
              )}

              <View
                style={[
                  styles.messageBubble,
                  msg.sender === 'user' ? styles.userBubble : styles.aiBubble,
                ]}
              >
                <Text
                  style={[
                    styles.messageText,
                    msg.sender === 'user' ? styles.userText : styles.aiText,
                  ]}
                >
                  {msg.text}
                </Text>

                {msg.citations && msg.citations.length > 0 && (
                  <View style={styles.citationsBox}>
                    <Text style={styles.citationsLabel}>Source: </Text>
                    {msg.citations.map((c, i) => (
                      <Text key={i} style={styles.citationPill}>
                        {c}
                      </Text>
                    ))}
                  </View>
                )}
              </View>
            </View>
          ))}

          {loading && (
            <View style={styles.aiThinkingBox}>
              <ActivityIndicator size="small" color={COLORS.primary} />
              <Text style={styles.thinkingText}>Evaluating report context...</Text>
            </View>
          )}

          <Text style={styles.aiDisclaimerFooter}>AI-generated information. Not a diagnosis.</Text>
        </ScrollView>

        {/* Input Bar */}
        <View style={styles.inputContainer}>
          <TextInput
            value={inputText}
            onChangeText={setInputText}
            placeholder="Ask a question about this report..."
            placeholderTextColor={COLORS.textMuted}
            style={styles.chatInput}
            onSubmitEditing={() => handleSend()}
          />
          <TouchableOpacity
            onPress={() => handleSend()}
            disabled={!inputText.trim() || loading}
            style={[
              styles.sendButton,
              inputText.trim() && !loading ? styles.sendButtonActive : styles.sendButtonDisabled,
            ]}
          >
            <Send size={18} color="#ffffff" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  messagesScroll: {
    flex: 1,
    padding: 16,
  },
  suggestedBox: {
    marginBottom: 14,
  },
  suggestedHeading: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.textSecondary,
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  suggestedRow: {
    flexDirection: 'row',
  },
  promptChip: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 12,
    marginRight: 8,
  },
  promptChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primaryDark,
  },
  messageRow: {
    flexDirection: 'row',
    marginBottom: 14,
  },
  userMessageRow: {
    justifyContent: 'flex-end',
  },
  aiMessageRow: {
    justifyContent: 'flex-start',
  },
  aiAvatar: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    marginTop: 2,
  },
  messageBubble: {
    maxWidth: '82%',
    padding: 14,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: COLORS.primary,
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 13,
    lineHeight: 18,
  },
  userText: {
    color: '#ffffff',
    fontWeight: '500',
  },
  aiText: {
    color: COLORS.textPrimary,
  },
  citationsBox: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  citationsLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  citationPill: {
    fontSize: 10,
    color: COLORS.primaryDark,
    backgroundColor: COLORS.primaryLight,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
  },
  aiThinkingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    alignSelf: 'flex-start',
    marginBottom: 10,
  },
  thinkingText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginLeft: 8,
  },
  aiDisclaimerFooter: {
    fontSize: 11,
    color: COLORS.textMuted,
    textAlign: 'center',
    fontStyle: 'italic',
    marginTop: 10,
    marginBottom: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.borderSubtle,
  },
  chatInput: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 13,
    color: COLORS.textPrimary,
    marginRight: 10,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonActive: {
    backgroundColor: COLORS.primary,
  },
  sendButtonDisabled: {
    backgroundColor: COLORS.border,
  },
});
