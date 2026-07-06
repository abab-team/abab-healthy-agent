import { Link } from "expo-router";
import type { Href } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
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

export default function AgentScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [brief, setBrief] = useState<AgentRunResponse | null>(null);
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
      setError(result.error?.message ?? "生成失败");
    }
  }

  return (
    <AppScreen>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>AI 健康管家</Text>
          <Text style={styles.subtitle}>整理系统内记录，辅助管理家庭健康事项。</Text>
        </View>
        <View style={styles.bot}>
          <Ionicons name="hardware-chip-outline" size={34} color={colors.primaryDark} />
        </View>
      </View>

      <SafetyNotice />

      <CardBase>
        <SectionHeader title="今天可以做什么？" action={session.dataMode === "api" ? "daily_health_brief 已接 API" : "mock"} />
        <ApiModeBadge mode={session.dataMode} />
        <Text style={styles.description}>
          本阶段仅把今日健康简报接入后端；写入类草稿与提醒仍为 mock 交互，正式写入前仍需要确认。
        </Text>
        <Pressable style={styles.button} onPress={runDailyBrief}>
          <Text style={styles.buttonText}>{loading ? "生成中..." : "生成今日健康简报"}</Text>
        </Pressable>
        {error ? <ApiErrorState message={error} /> : null}
        {brief ? (
          <View style={styles.briefBox}>
            <Text style={styles.logTitle}>Trace：{brief.trace_id}</Text>
            <Text style={styles.description}>{brief.generated_content}</Text>
            <Link href={routes.agentRun(brief.trace_id)} style={styles.link}>查看本次 Agent Run</Link>
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
              {action.workflowType === "daily_health_brief" ? (
                <ApiModeBadge mode={session.dataMode} label={session.dataMode === "api" ? "API" : "mock"} />
              ) : (
                <MockDataBadge label="mock / 不真实提交" />
              )}
            </View>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="待确认草稿" action="写入工作流仍为 mock ›" />
        <MockDataBadge label="mock / 不真实提交" />
        {pendingDrafts.map((draft) => (
          <Link key={draft.id} href={routes.drafts}>
            <DraftReviewCard createdAt={draft.createdAt} summary={draft.summary} title={draft.title} type={draft.type} />
          </Link>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="AI 执行记录" action="安全摘要 ›" />
        {agentLogs.map((log) => (
          <Link key={log.id} href={routes.agentRun(brief?.trace_id ?? agentRun.id)}>
            <View style={styles.logRow}>
              <Ionicons name={log.status === "已完成" ? "checkmark-circle" : "time-outline"} size={22} color={log.status === "已完成" ? colors.primary : colors.warning} />
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
        run={(brief?.trace_id ?? agentRun.id).replace("run-", "Run ")}
        safetyChecks={agentRun.safetyChecks}
        toolCalls={brief?.tool_calls_count ?? agentRun.toolCalls}
      />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  bot: {
    alignItems: "center",
    backgroundColor: colors.blue,
    borderRadius: 28,
    height: 62,
    justifyContent: "center",
    width: 62
  },
  actionWrap: {
    width: "48%"
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
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 6
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  }
});
