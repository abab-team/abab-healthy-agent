import { Link } from "expo-router";
import type { Href } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useState } from "react";
import { AgentActionCard } from "@/components/cards/AgentActionCard";
import { CardBase } from "@/components/cards/CardBase";
import { DraftReviewCard } from "@/components/cards/DraftReviewCard";
import { TraceDebugPanel } from "@/components/cards/TraceDebugPanel";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { MockDataBadge } from "@/components/common/MockDataBadge";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { agentActions, agentLogs, agentRun, pendingDrafts } from "@/constants/mockData";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse } from "@/types/api";

function shortId(id: string): string {
  return id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-6)}` : id;
}

function actionBadge(mode: "api" | "mock", workflowType: string): string {
  if (mode !== "api") {
    return workflowType === "daily_health_brief" ? "演示简报" : "演示预览";
  }
  return workflowType === "daily_health_brief" ? "已接入后端" : "写入前需确认";
}

export default function AgentScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [brief, setBrief] = useState<AgentRunResponse | null>(null);
  const [query, setQuery] = useState("最近一周我的血压记录怎么样？");
  const [queryResult, setQueryResult] = useState<AgentRunResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runDailyBrief() {
    setLoading(true);
    setError(null);
    const result = await provider.runDailyHealthBrief(session.currentUserId);
    setLoading(false);
    if (result.ok && result.data) {
      setBrief(result.data);
    } else {
      setError(result.error?.message ?? "生成失败，请稍后重试。");
    }
  }

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
      setQueryError(result.error?.message ?? "查询失败，请稍后重试。");
    }
  }

  return (
    <AppScreen>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.title}>AI 健康管家</Text>
          <Text style={styles.subtitle}>整理系统内记录，帮助你更轻松地管理家庭健康事项。</Text>
        </View>
        <View style={styles.bot}>
          <Ionicons name="hardware-chip-outline" size={34} color={colors.primaryDark} />
        </View>
      </View>

      <SafetyNotice />

      <CardBase>
        <SectionHeader title="问问系统内记录" action={session.dataMode === "api" ? "API 查询" : "演示查询"} />
        <Text style={styles.description}>
          可以询问血压、睡眠、步数、症状、健康事件、文档和提醒等系统内记录。当前入口只允许受控 chat workflow，不开放通用工具调用。
        </Text>
        <TextInput
          multiline
          onChangeText={setQuery}
          placeholder="例如：最近一周我的血压记录怎么样？"
          placeholderTextColor={colors.textMuted}
          style={styles.queryInput}
          value={query}
        />
        <View style={styles.suggestionRow}>
          {["我最近一周睡眠记录怎么样？", "系统内有哪些待办提醒？", "最近有没有健康文档记录？"].map((item) => (
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
          <View style={styles.briefBox}>
            <Text style={styles.logTitle}>查询结果：{shortId(queryResult.trace_id)}</Text>
            <Text style={styles.description}>{queryResult.generated_content}</Text>
            <Link href={routes.agentRun(queryResult.trace_id)} style={styles.link}>
              查看执行详情
            </Link>
          </View>
        ) : null}
      </CardBase>

      <CardBase>
        <SectionHeader title="今天可以做什么？" action={session.dataMode === "api" ? "后端已连接" : "演示数据"} />
        <ApiModeBadge mode={session.dataMode} />
        <Text style={styles.description}>
          今日健康简报、症状草稿、健康事件草稿和健康提醒都经过受控流程。预览不会写入，确认后也只会创建待确认草稿或普通健康提醒。
        </Text>
        <Pressable style={styles.button} onPress={runDailyBrief}>
          <Text style={styles.buttonText}>{loading ? "正在整理..." : "生成今日健康简报"}</Text>
        </Pressable>
        {error ? <ApiErrorState message={error} /> : null}
        {brief ? (
          <View style={styles.briefBox}>
            <Text style={styles.logTitle}>执行记录：{shortId(brief.trace_id)}</Text>
            <Text style={styles.description}>{brief.generated_content}</Text>
            <Link href={routes.agentRun(brief.trace_id)} style={styles.link}>
              查看执行详情
            </Link>
          </View>
        ) : null}
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
              <ApiModeBadge mode={session.dataMode} label={actionBadge(session.dataMode, action.workflowType)} />
            </View>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="待确认草稿" action="查看列表" />
        <MockDataBadge label="草稿列表演示中" />
        <Text style={styles.description}>草稿正式确认入库仍在后续接入，本页不会直接创建正式健康事实。</Text>
        {pendingDrafts.map((draft) => (
          <Link key={draft.id} href={routes.drafts}>
            <DraftReviewCard createdAt={draft.createdAt} summary={draft.summary} title={draft.title} type={draft.type} />
          </Link>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="执行记录" action="安全摘要" />
        {agentLogs.map((log) => (
          <Link key={log.id} href={routes.agentRun(brief?.trace_id ?? agentRun.id)}>
            <View style={styles.logRow}>
              <Ionicons
                name={log.status === "已完成" ? "checkmark-circle" : "time-outline"}
                size={22}
                color={log.status === "已完成" ? colors.primary : colors.warning}
              />
              <View style={styles.logCopy}>
                <Text style={styles.logTitle}>{log.title}</Text>
                <Text style={styles.logTime}>{log.time}</Text>
              </View>
              <StatusBadge label={log.status} tone={log.status === "已完成" ? "mint" : "orange"} />
            </View>
          </Link>
        ))}
      </CardBase>

      <TraceDebugPanel
        href={routes.agentRun(brief?.trace_id ?? agentRun.id)}
        run={shortId(brief?.trace_id ?? agentRun.id)}
        safetyChecks={agentRun.safetyChecks}
        toolCalls={brief?.tool_calls_count ?? agentRun.toolCalls}
      />
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
  briefBox: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: 14,
    marginTop: 12,
    padding: 12
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
  logCopy: {
    flex: 1
  },
  logRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    paddingVertical: 11
  },
  logTime: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 3
  },
  logTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "800"
  },
  recommendGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 14
  },
  queryInput: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
    marginTop: 12,
    minHeight: 88,
    paddingHorizontal: 12,
    paddingVertical: 10,
    textAlignVertical: "top"
  },
  suggestionButton: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: 999,
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
