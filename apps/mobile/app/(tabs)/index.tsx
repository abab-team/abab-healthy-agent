import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useState } from "react";
import { CardBase } from "@/components/cards/CardBase";
import { QuickActionGrid } from "@/components/cards/QuickActionGrid";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { currentUser, reminders } from "@/constants/mockData";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse } from "@/types/api";

const todayMetrics = [
  { label: "睡眠", value: "6.8 小时", note: "最近 7 天记录", icon: "moon-outline", tone: "blue" },
  { label: "步数", value: "6,420", note: "今日演示数据", icon: "footsteps-outline", tone: "mint" },
  { label: "心率", value: "72 次/分", note: "最近一次记录", icon: "heart-outline", tone: "purple" },
  { label: "血压", value: "120/78", note: "系统内最近记录", icon: "pulse-outline", tone: "orange" }
] as const;

const familySummary = [
  "爸爸：最近有血压记录摘要",
  "妈妈：有一个复查提醒",
  "家庭共享：按成员权限展示"
];

function shortId(id: string): string {
  return id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-6)}` : id;
}

export default function HomeScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [brief, setBrief] = useState<AgentRunResponse | null>(null);
  const [briefError, setBriefError] = useState<string | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);

  async function runBrief() {
    setBriefLoading(true);
    setBriefError(null);
    const result = await provider.runDailyHealthBrief(session.currentUserId);
    setBriefLoading(false);
    if (result.ok && result.data) {
      setBrief(result.data);
    } else {
      setBriefError(result.error?.message ?? "简报生成失败，请稍后再试。");
    }
  }

  return (
    <AppScreen>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.greeting}>早上好，{currentUser.name}</Text>
          <Text style={styles.subtitle}>这是你的系统内健康记录概览，仅供日常整理，不替代医生判断。</Text>
        </View>
        <StatusBadge label={session.dataMode === "api" ? "API 数据" : "演示数据"} tone="mint" />
      </View>

      <CardBase style={styles.heroCard}>
        <SectionHeader title="我的今日状态" action="基于系统内记录" />
        <View style={styles.metricGrid}>
          {todayMetrics.map((metric) => (
            <View key={metric.label} style={[styles.metricCard, styles[metric.tone]]}>
              <Ionicons name={metric.icon} size={22} color={colors.primaryDark} />
              <Text style={styles.metricLabel}>{metric.label}</Text>
              <Text style={styles.metricValue}>{metric.value}</Text>
              <Text style={styles.metricNote}>{metric.note}</Text>
            </View>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="AI 今日简报" action={session.dataMode === "api" ? "已接入" : "演示中"} />
        <Text style={styles.paragraph}>整理今天和最近几天的系统内记录；不会给出诊断、处方或用药剂量建议。</Text>
        <Pressable style={styles.primaryButton} onPress={runBrief}>
          <Text style={styles.primaryButtonText}>{briefLoading ? "正在整理..." : "生成今日健康简报"}</Text>
        </Pressable>
        {briefError ? <ApiErrorState message={briefError} /> : null}
        {brief ? (
          <View style={styles.resultBox}>
            <Text style={styles.resultTitle}>Trace：{shortId(brief.trace_id)}</Text>
            <Text style={styles.paragraph}>{brief.generated_content}</Text>
            <Link href={routes.agentRun(brief.trace_id)} style={styles.link}>
              查看执行详情
            </Link>
          </View>
        ) : null}
      </CardBase>

      <CardBase>
        <SectionHeader title="我的关注提醒" action="普通健康提醒" />
        {reminders.map((item) => (
          <Text key={item.id} style={styles.listItem}>
            {item.title} · {item.time}
          </Text>
        ))}
        <Text style={styles.smallNote}>提醒不是急救服务。如遇紧急情况，请联系医生或当地急救服务。</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="快速记录" action="演示模式" />
        <Text style={styles.paragraph}>演示模式下不会提交真实数据；API 模式下写入仍需要 preview / confirm。</Text>
        <QuickActionGrid />
      </CardBase>

      <CardBase>
        <SectionHeader title="家庭轻摘要" action="查看家庭" />
        {familySummary.map((item) => (
          <Text key={item} style={styles.listItem}>
            {item}
          </Text>
        ))}
        <Link href={routes.family} style={styles.link}>
          进入家庭页
        </Link>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  blue: { backgroundColor: colors.blue },
  greeting: {
    color: colors.text,
    fontSize: 23,
    fontWeight: "900"
  },
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  headerCopy: {
    flex: 1,
    paddingRight: 12
  },
  heroCard: {
    backgroundColor: "#e9fbf7"
  },
  link: {
    color: colors.primaryDark,
    fontSize: 13,
    fontWeight: "800",
    marginTop: 10
  },
  listItem: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    color: colors.text,
    fontSize: 13,
    lineHeight: 20,
    paddingVertical: 11
  },
  metricCard: {
    borderRadius: 16,
    padding: 12,
    width: "48%"
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  metricLabel: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 8
  },
  metricNote: {
    color: colors.textMuted,
    fontSize: 11,
    marginTop: 4
  },
  metricValue: {
    color: colors.text,
    fontSize: 19,
    fontWeight: "900",
    marginTop: 3
  },
  mint: { backgroundColor: colors.mint },
  orange: { backgroundColor: colors.orange },
  paragraph: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8
  },
  primaryButton: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    marginTop: 12,
    paddingVertical: 12
  },
  primaryButtonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "800",
    textAlign: "center"
  },
  purple: { backgroundColor: colors.purple },
  resultBox: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: 14,
    marginTop: 12,
    padding: 12
  },
  resultTitle: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "800"
  },
  smallNote: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 19,
    marginTop: 7
  }
});
