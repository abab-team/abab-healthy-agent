import { Link } from "expo-router";
import type { Href } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { AgentActionCard } from "@/components/cards/AgentActionCard";
import { CardBase } from "@/components/cards/CardBase";
import { DraftReviewCard } from "@/components/cards/DraftReviewCard";
import { TraceDebugPanel } from "@/components/cards/TraceDebugPanel";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { agentActions, agentLogs, agentRun, pendingDrafts } from "@/constants/mockData";
import { routes } from "@/lib/routes";

export default function AgentScreen() {
  return (
    <AppScreen>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>AI 健康管家</Text>
          <Text style={styles.subtitle}>整理系统内记录，辅助你管理家庭健康事项。</Text>
        </View>
        <View style={styles.bot}>
          <Ionicons name="hardware-chip-outline" size={34} color={colors.primaryDark} />
        </View>
      </View>

      <SafetyNotice />

      <CardBase>
        <SectionHeader title="今天可以做什么？" />
        <Text style={styles.description}>
          AI 可以帮你整理记录、生成草稿和提醒建议，让健康管理更轻松。
        </Text>
        <View style={styles.recommendGrid}>
          {agentActions.map((action) => (
            <AgentActionCard
              key={action.id}
              title={action.title}
              description={action.description}
              href={action.href as Href}
              icon={action.icon as keyof typeof Ionicons.glyphMap}
              tone={action.tone as "mint" | "blue" | "orange" | "purple"}
            />
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="待确认草稿" action="查看全部 ›" />
        {pendingDrafts.map((draft) => (
          <Link key={draft.id} href={routes.drafts}>
            <DraftReviewCard
              type={draft.type}
              title={draft.title}
              createdAt={draft.createdAt}
              summary={draft.summary}
            />
          </Link>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="AI 执行记录" action="查看全部 ›" />
        {agentLogs.map((log) => (
          <Link key={log.id} href={routes.agentRun(agentRun.id)}>
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
        run={agentRun.id.replace("run-", "Run ")}
        toolCalls={agentRun.toolCalls}
        safetyChecks={agentRun.safetyChecks}
        href={routes.agentRun(agentRun.id)}
      />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 6
  },
  bot: {
    alignItems: "center",
    backgroundColor: colors.blue,
    borderRadius: 28,
    height: 62,
    justifyContent: "center",
    width: 62
  },
  description: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8
  },
  recommendGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 14
  },
  logRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    paddingVertical: 11
  },
  logCopy: {
    flex: 1
  },
  logTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "800"
  },
  logTime: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 3
  }
});
