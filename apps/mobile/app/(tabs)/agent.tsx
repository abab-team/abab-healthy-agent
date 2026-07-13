import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ChatBubble } from "@/components/common/ChatBubble";
import { InlineSafetyNotice } from "@/components/common/InlineSafetyNotice";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse } from "@/types/api";

const suggestions = ["我最近一周睡眠怎么样？", "爸爸最近身体情况怎么样？", "帮我整理体检资料", "帮我记录今天头痛"];
type SuggestedAction = NonNullable<AgentRunResponse["suggested_action"]>;
type ConversationMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  suggestedAction?: SuggestedAction | null;
};

const actionLabels: Record<SuggestedAction, string> = {
  health_alert: "整理健康提醒",
  health_event_draft: "整理健康事件草稿",
  symptom_draft: "整理症状草稿"
};

export default function AgentScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const router = useRouter();
  const scrollRef = useRef<ScrollView>(null);
  const [query, setQuery] = useState("");
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [familyId, setFamilyId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  useEffect(() => {
    let active = true;
    void (async () => {
      const family = await provider.getFamilyOverview();
      if (active && family.ok && family.data?.family.id && family.data.family.id !== "empty") {
        setFamilyId(family.data.family.id);
      }
      const sessions = await provider.listAgentSessions();
      const latest = sessions.ok ? sessions.data?.[0] : undefined;
      if (!latest || !active) return;
      const history = await provider.listAgentSessionMessages(latest.id);
      if (!active || !history.ok || !history.data) return;
      setChatSessionId(latest.id);
      setMessages(history.data.map((item) => ({
        content: item.content_summary,
        id: item.id,
        role: item.role === "user" ? "user" : "assistant"
      })));
    })();
    return () => { active = false; };
  }, [provider]);

  useEffect(() => {
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(timer);
  }, [messages, queryLoading]);

  function openSuggestedAction(action: SuggestedAction) {
    if (action === "symptom_draft") router.push(routes.createSymptomDraft);
    if (action === "health_event_draft") router.push(routes.createHealthEventDraft);
    if (action === "health_alert") router.push(routes.createAlert);
  }

  async function runChatQuery(question = query) {
    const normalized = question.trim();
    if (!normalized || queryLoading) return;
    const userMessage: ConversationMessage = { content: normalized, id: `user-${Date.now()}`, role: "user" };
    setMessages((items) => [...items, userMessage]);
    setQuery("");
    setQueryLoading(true);
    setQueryError(null);
    const result = await provider.runChatHealthQuery({
      familyId,
      question: normalized,
      sessionId: chatSessionId,
      targetUserId: session.currentUserId
    });
    setQueryLoading(false);
    if (result.ok && result.data) {
      const run = result.data;
      setChatSessionId(run.session_id ?? chatSessionId);
      setMessages((items) => [...items, {
        content: run.generated_content ?? run.message ?? "暂时没有可展示的回复。",
        id: `assistant-${Date.now()}`,
        role: "assistant",
        suggestedAction: run.suggested_action
      }]);
      return;
    }
    setQueryError(result.error?.message ?? "暂时无法回复这条消息，请稍后再试。");
  }

  const composer = <View>
    <View style={styles.composer}>
      <TextInput
        multiline
        onChangeText={setQuery}
        placeholder="和 AI 健康管家聊聊…"
        placeholderTextColor={theme.colors.subtle}
        style={styles.input}
        value={query}
      />
      <Pressable disabled={queryLoading || !query.trim()} onPress={() => void runChatQuery()} style={[styles.sendButton, (queryLoading || !query.trim()) ? styles.sendButtonDisabled : null]}>
        <Ionicons color="#FFFFFF" name="arrow-up" size={20} />
      </Pressable>
    </View>
    <Text style={styles.composerHint}>{queryLoading ? "正在准备回复…" : "涉及家人记录时，我会先核对家庭共享权限。"}</Text>
  </View>;

  return <AppScreen footer={composer} scroll={false}>
    <ScreenHeader subtitle="我可以帮你整理自己和家人的健康记录。" title="AI 健康管家" />
    <ScrollView ref={scrollRef} contentContainerStyle={styles.chatContent} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} style={styles.chatScroll}>
      {messages.length === 0 ? <>
        <ChatBubble content="你好，Gala 👋\n\n今天想聊点什么？我可以陪你说说话，也能在权限允许的范围内帮你整理自己和家人的健康记录。" role="assistant" />
        <View style={styles.questionHeader}><Text style={styles.sectionTitle}>你可以这样问</Text><Text style={styles.sectionCaption}>连续追问会沿用当前对话上下文</Text></View>
        <View style={styles.suggestions}>{suggestions.map((suggestion) => <Pressable key={suggestion} onPress={() => void runChatQuery(suggestion)} style={styles.suggestion}><Text style={styles.suggestionText}>{suggestion}</Text><Ionicons color={theme.colors.primaryDark} name="arrow-up-outline" size={15} /></Pressable>)}</View>
      </> : messages.map((message) => <View key={message.id} style={styles.messageGroup}>
        <ChatBubble content={message.content} role={message.role} />
        {message.role === "assistant" && message.suggestedAction ? <Pressable onPress={() => openSuggestedAction(message.suggestedAction!)} style={styles.actionButton}><Text style={styles.actionButtonText}>{actionLabels[message.suggestedAction]}</Text><Ionicons color={theme.colors.primaryDark} name="arrow-forward" size={15} /></Pressable> : null}
      </View>)}
      {queryLoading ? <View style={styles.typing}><View style={styles.typingDot} /><View style={styles.typingDot} /><View style={styles.typingDot} /></View> : null}
      {queryError ? <ApiErrorState message={queryError} /> : null}
      <InlineSafetyNotice />
    </ScrollView>
  </AppScreen>;
}

const styles = StyleSheet.create({
  actionButton: { alignItems: "center", alignSelf: "flex-start", backgroundColor: theme.colors.tealSoft, borderColor: theme.colors.primary, borderRadius: theme.radius.pill, borderWidth: 1, flexDirection: "row", gap: 6, paddingHorizontal: 12, paddingVertical: 8 },
  actionButtonText: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  chatContent: { gap: 12, paddingBottom: 18, paddingHorizontal: theme.spacing.lg },
  chatScroll: { flex: 1, marginHorizontal: -theme.spacing.lg },
  composer: { alignItems: "flex-end", backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, flexDirection: "row", gap: 8, padding: 7 },
  composerHint: { color: theme.colors.subtle, fontSize: 11, lineHeight: 17, paddingHorizontal: 4 },
  input: { color: theme.colors.ink, flex: 1, fontSize: 14, lineHeight: 20, maxHeight: 96, minHeight: 42, paddingHorizontal: 8, paddingVertical: 10, textAlignVertical: "top" },
  messageGroup: { gap: 7 },
  questionHeader: { marginTop: 2 },
  sectionCaption: { color: theme.colors.subtle, fontSize: 12, marginTop: 4 },
  sectionTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" },
  sendButton: { alignItems: "center", backgroundColor: theme.colors.primary, borderRadius: theme.radius.pill, height: 42, justifyContent: "center", width: 42 },
  sendButtonDisabled: { opacity: 0.45 },
  suggestion: { alignItems: "center", alignSelf: "flex-start", backgroundColor: theme.colors.tealSoft, borderRadius: theme.radius.pill, flexDirection: "row", gap: 7, paddingHorizontal: 12, paddingVertical: 9 },
  suggestionText: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "800" },
  suggestions: { alignItems: "flex-start", gap: 8 },
  typing: { alignItems: "center", backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.pill, borderWidth: 1, flexDirection: "row", gap: 5, paddingHorizontal: 13, paddingVertical: 10, width: 66 },
  typingDot: { backgroundColor: theme.colors.primary, borderRadius: 3, height: 6, width: 6 }
});
