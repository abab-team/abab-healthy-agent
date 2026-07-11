import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { useEffect, useRef, useState } from "react";
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

const suggestions = ["我最近一周的睡眠记录怎么样？", "爸爸最近有哪些提醒？", "我上传过哪些检查资料？"];
type ConversationMessage = { id: string; role: "user" | "assistant"; content: string };

export default function AgentScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const scrollRef = useRef<ScrollView>(null);
  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState<AgentRunResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(timer);
  }, [messages, queryLoading]);

  async function runChatQuery(question = query) {
    const normalized = question.trim();
    if (!normalized || queryLoading) return;
    const userMessage: ConversationMessage = { content: normalized, id: `user-${Date.now()}`, role: "user" };
    setMessages((items) => [...items, userMessage]);
    setQuery("");
    setQueryLoading(true);
    setQueryError(null);
    const result = await provider.runChatHealthQuery({ question: normalized, sessionId: chatSessionId, targetUserId: session.currentUserId });
    setQueryLoading(false);
    if (result.ok && result.data) {
      const run = result.data;
      setQueryResult(run);
      setChatSessionId(run.session_id ?? chatSessionId);
      setMessages((items) => [...items, { content: run.generated_content ?? run.message ?? "系统内暂无可展示的整理结果。", id: `assistant-${Date.now()}`, role: "assistant" }]);
      return;
    }
    setQueryError(result.error?.message ?? "暂时无法整理这条记录，请稍后再试。");
  }

  const composer = <View><View style={styles.composer}><TextInput multiline onChangeText={setQuery} placeholder="发送健康记录相关问题…" placeholderTextColor={theme.colors.subtle} style={styles.input} value={query} /><Pressable disabled={queryLoading || !query.trim()} onPress={() => void runChatQuery()} style={[styles.sendButton, (queryLoading || !query.trim()) ? styles.sendButtonDisabled : null]}><Ionicons color="#FFFFFF" name="arrow-up" size={20} /></Pressable></View><Text style={styles.composerHint}>{queryLoading ? "正在整理系统内记录…" : "仅支持受控健康记录查询，不提供诊断或处方建议。"}</Text></View>;

  return <AppScreen footer={composer} scroll={false}>
    <ScreenHeader subtitle="你的私人健康记录整理助手。" title="AI 健康管家" />
    <ScrollView ref={scrollRef} contentContainerStyle={styles.chatContent} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} style={styles.chatScroll}>
      {messages.length === 0 ? <><View style={styles.questionHeader}><Text style={styles.sectionTitle}>你可以这样问</Text><Text style={styles.sectionCaption}>连续追问会沿用当前对话上下文</Text></View><View style={styles.suggestions}>{suggestions.map((suggestion) => <Pressable key={suggestion} onPress={() => void runChatQuery(suggestion)} style={styles.suggestion}><Text style={styles.suggestionText}>{suggestion}</Text><Ionicons color={theme.colors.primaryDark} name="arrow-up-outline" size={15} /></Pressable>)}</View><ChatBubble content="你好，Gala 👋\n\n我可以帮你整理健康记录、查看趋势、准备就医资料。" role="assistant" /><InlineSafetyNotice /></> : messages.map((message) => <View key={message.id} style={styles.messageGroup}><ChatBubble content={message.content} role={message.role} />{message.role === "assistant" ? <InlineSafetyNotice /> : null}</View>)}
      {queryLoading ? <View style={styles.typing}><View style={styles.typingDot} /><View style={styles.typingDot} /><View style={styles.typingDot} /></View> : null}
      {queryError ? <ApiErrorState message={queryError} /> : null}
      {queryResult ? <Link href={routes.agentRun(queryResult.trace_id)} style={styles.runLink}>查看本次整理记录</Link> : null}
    </ScrollView>
  </AppScreen>;
}

const styles = StyleSheet.create({
  chatContent: { gap: 12, paddingBottom: 18, paddingHorizontal: theme.spacing.lg },
  chatScroll: { flex: 1, marginHorizontal: -theme.spacing.lg },
  composer: { alignItems: "flex-end", backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, flexDirection: "row", gap: 8, padding: 7 },
  composerHint: { color: theme.colors.subtle, fontSize: 11, lineHeight: 17, paddingHorizontal: 4 },
  input: { color: theme.colors.ink, flex: 1, fontSize: 14, lineHeight: 20, maxHeight: 96, minHeight: 42, paddingHorizontal: 8, paddingVertical: 10, textAlignVertical: "top" },
  messageGroup: { gap: 7 },
  questionHeader: { marginTop: 2 },
  runLink: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900", marginLeft: 4 },
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
