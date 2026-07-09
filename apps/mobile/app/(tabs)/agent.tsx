import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import type { Href } from "expo-router";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useState } from "react";
import { AgentActionCard } from "@/components/cards/AgentActionCard";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { agentActions } from "@/constants/mockData";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse } from "@/types/api";

const suggestions = [
  "我最近一周睡眠记录怎么样？",
  "爸爸最近一周血压记录怎么样？",
  "最近有哪些待办提醒？",
  "我上传过哪些检查资料？"
];

function shortId(id: string): string {
  return id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-6)}` : id;
}

export default function AgentScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [query, setQuery] = useState(suggestions[0]);
  const [queryResult, setQueryResult] = useState<AgentRunResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);

  async function runChatQuery() {
    const normalized = query.trim();
    if (!normalized) {
      setQueryError("请先输入想查询的系统内健康记录。");
      return;
    }
    setQueryLoading(true);
    setQueryError(null);
    const result = await provider.runChatHealthQuery({
      question: normalized,
      targetUserId: session.currentUserId
    });
    setQueryLoading(false);
    if (result.ok && result.data) {
      setQueryResult(result.data);
    } else {
      setQueryError(result.error?.message ?? "查询失败，请稍后再试。");
    }
  }

  return (
    <AppScreen>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.title}>AI 健康管家</Text>
          <Text style={styles.subtitle}>问问系统内记录，整理健康简报和待确认草稿。</Text>
        </View>
        <View style={styles.bot}>
          <Ionicons name="chatbubble-ellipses-outline" size={32} color={colors.primaryDark} />
        </View>
      </View>

      <SafetyNotice />

      <CardBase style={styles.chatCard}>
        <SectionHeader title="问问系统内记录" action={session.dataMode === "api" ? "API 已接入" : "演示数据"} />
        <Text style={styles.description}>回答只基于系统内记录；记录可能不完整，不替代医生判断。</Text>
        <TextInput
          multiline
          onChangeText={setQuery}
          placeholder="例如：我最近一周血压记录怎么样？"
          placeholderTextColor={colors.textMuted}
          style={styles.queryInput}
          value={query}
        />
        <View style={styles.suggestionRow}>
          {suggestions.map((item) => (
            <Pressable key={item} onPress={() => setQuery(item)} style={styles.suggestionButton}>
              <Text style={styles.suggestionText}>{item}</Text>
            </Pressable>
          ))}
        </View>
        <Pressable style={styles.button} onPress={runChatQuery}>
          <Text style={styles.buttonText}>{queryLoading ? "正在查询..." : "查询系统内记录"}</Text>
        </Pressable>
        {queryError ? <ApiErrorState message={queryError} /> : null}
        {queryResult ? (
          <View style={styles.resultBox}>
            <Text style={styles.resultTitle}>回答摘要 · {shortId(queryResult.trace_id)}</Text>
            <Text style={styles.description}>{queryResult.generated_content}</Text>
            <Link href={routes.agentRun(queryResult.trace_id)} style={styles.link}>
              查看执行详情
            </Link>
          </View>
        ) : null}
      </CardBase>

      <CardBase>
        <SectionHeader title="常用能力" action="写入前会确认" />
        <View style={styles.recommendGrid}>
          {agentActions.map((action) => (
            <View key={action.id} style={styles.actionWrap}>
              <AgentActionCard
                description={action.description}
                href={action.href as Href}
                icon={action.icon as keyof typeof Ionicons.glyphMap}
                title={action.title}
                tone={action.tone as "mint" | "blue" | "orange" | "purple"}
              />
            </View>
          ))}
        </View>
        <Text style={styles.description}>预览不会写入；确认后也只会创建待确认草稿或普通健康提醒。提醒不是急救。</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="历史记录" action="安全摘要" />
        <Text style={styles.description}>执行记录、工具摘要、安全检查和图编排摘要放在详情页查看，主页面不展示内部调试参数。</Text>
        <Link href={routes.agentRun("run-12")} style={styles.link}>
          查看最近一次执行记录
        </Link>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  actionWrap: {
    width: "48%"
  },
  bot: {
    alignItems: "center",
    backgroundColor: colors.blue,
    borderRadius: 28,
    height: 62,
    justifyContent: "center",
    width: 62
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    marginTop: 12,
    paddingVertical: 12
  },
  buttonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "800",
    textAlign: "center"
  },
  chatCard: {
    backgroundColor: "#f4fbff"
  },
  description: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  headerCopy: {
    flex: 1,
    paddingRight: 12
  },
  link: {
    color: colors.primaryDark,
    fontSize: 13,
    fontWeight: "800",
    marginTop: 10
  },
  queryInput: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
    marginTop: 12,
    minHeight: 86,
    paddingHorizontal: 12,
    paddingVertical: 10,
    textAlignVertical: "top"
  },
  recommendGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 14
  },
  resultBox: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    marginTop: 12,
    padding: 12
  },
  resultTitle: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "800"
  },
  suggestionButton: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 8
  },
  suggestionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 10
  },
  suggestionText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700"
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 19,
    marginTop: 6
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  }
});
