import { Ionicons } from "@expo/vector-icons";
import { Link, router } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { HealthTrendSection } from "@/components/cards/HealthTrendSection";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { MetricTile } from "@/components/common/MetricTile";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { currentUser } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse } from "@/types/api";

const metrics = [
  { icon: "moon-outline", label: "睡眠", note: "最近 7 天记录", tone: "blue", value: "7.2 小时" },
  { icon: "footsteps-outline", label: "步数", note: "今日系统内记录", tone: "teal", value: "6,100 步" },
  { icon: "heart-outline", label: "心率", note: "最近一次记录", tone: "coral", value: "72 次/分" },
  { icon: "pulse-outline", label: "血压", note: "系统内最近记录", tone: "lavender", value: "118/76" },
  { icon: "scale-outline", label: "体重", note: "最近一次记录", tone: "teal", value: "62.2 kg", wide: true }
] as const;

const personalRecentRecords = [
  { detail: "7 小时 20 分钟", title: "睡眠记录", tone: "teal" },
  { detail: "待确认草稿", title: "症状记录", tone: "coral" },
  { detail: "体检资料已保存", title: "文档记录", tone: "blue" },
  { detail: "62.2 kg", title: "体重记录", tone: "lavender" }
] as const;

const personalBriefFallback = "根据你最近 7 天的系统内记录，已整理睡眠、血压与体重等个人健康数据。记录可能不完整，本小结仅用于日常整理，不替代医生判断。";

function shortId(id: string): string {
  return id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-6)}` : id;
}

function formatGeneratedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "刚刚";
  }
  return date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" });
}

export default function HomeScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [brief, setBrief] = useState<AgentRunResponse | null>(null);
  const [briefGeneratedAt, setBriefGeneratedAt] = useState<string | null>(null);
  const [briefError, setBriefError] = useState<string | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const briefContent = brief?.generated_content ?? personalBriefFallback;
  const trendResource = useApiResource(() => provider.getArchiveTrends(), [session.currentUserId]);

  useEffect(() => {
    let active = true;
    async function loadLatestBrief() {
      const result = await provider.getLatestDailyHealthBrief();
      if (active && result.ok && result.data) {
        setBrief({
          generated_content: result.data.generated_content,
          status: "completed",
          trace_id: result.data.trace_id,
          workflow_type: "daily_health_brief"
        });
        setBriefGeneratedAt(result.data.generated_at);
      }
    }
    void loadLatestBrief();
    return () => {
      active = false;
    };
  }, [session.currentUserId, session.dataMode]);

  async function runBrief() {
    setBriefLoading(true);
    setBriefError(null);
    const result = await provider.runDailyHealthBrief(session.currentUserId);
    setBriefLoading(false);
    if (result.ok && result.data) {
      setBrief(result.data);
      setBriefGeneratedAt(new Date().toISOString());
      return;
    }
    setBriefError(result.error?.message ?? "健康小结暂时无法整理，请稍后再试。");
  }

  return (
    <AppScreen>
      <ScreenHeader
        subtitle="今天也把健康记录照顾得井井有条。"
        title={`早上好，${currentUser.name}`}
        trailing={<StatusBadge label={session.dataMode === "api" ? "数据已连接" : "演示数据"} tone="mint" />}
      />

      <CardBase style={styles.overviewCard}>
        <View style={styles.overviewHeader}>
          <View>
            <Text style={styles.cardTitle}>今日健康概览</Text>
            <Text style={styles.cardCaption}>基于系统内已有记录整理</Text>
          </View>
          <Ionicons color={theme.colors.primary} name="calendar-outline" size={22} />
        </View>
        <View style={styles.metricGrid}>
          {metrics.map((metric) => (
            <MetricTile key={metric.label} {...metric} />
          ))}
        </View>
        <Pressable onPress={() => router.push(routes.recordHealthMetric)} style={styles.metricEntry}>
          <Ionicons color={theme.colors.primaryDark} name="add-circle-outline" size={18} />
          <Text style={styles.metricEntryText}>记录健康指标</Text>
        </Pressable>
      </CardBase>

      <HealthTrendSection error={trendResource.error} loading={trendResource.loading} trends={trendResource.data} />

      <CardBase style={styles.briefCard}>
        <View style={styles.briefHeading}>
          <View style={styles.briefIcon}>
            <Ionicons color={theme.colors.primaryDark} name="sparkles-outline" size={23} />
          </View>
          <View style={styles.briefCopy}>
            <Text style={styles.cardTitle}>AI 健康小结</Text>
            <Text style={styles.cardCaption}>只基于系统内记录，不替代医生判断。</Text>
          </View>
        </View>
        <View style={styles.resultBox}>
          <Text style={styles.resultText}>{briefContent}</Text>
          {briefGeneratedAt ? <Text style={styles.generatedAt}>最近生成：{formatGeneratedAt(briefGeneratedAt)}</Text> : null}
          {brief ? (
            <Link href={routes.agentRun(brief.trace_id)} style={styles.detailLink}>
              查看本次整理 · {shortId(brief.trace_id)}
            </Link>
          ) : null}
        </View>
        <PrimaryButton label={briefLoading ? "正在更新..." : "更新个人健康小结"} disabled={briefLoading} onPress={runBrief} />
        {briefError ? <ApiErrorState message={briefError} /> : null}
      </CardBase>

      <CardBase>
        <View style={styles.sectionRow}>
          <Text style={styles.cardTitle}>最近记录</Text>
          <Link href={routes.archive} style={styles.detailLink}>
            查看档案
          </Link>
        </View>
        {personalRecentRecords.map((record, index) => (
          <View key={record.title} style={styles.recordRow}>
            <View style={[styles.recordDot, index === 0 ? styles.dotTeal : null]} />
            <View style={styles.recordCopy}>
              <Text style={styles.recordTitle}>{record.title}</Text>
              <Text style={styles.recordDetail}>{record.detail}</Text>
            </View>
            <Ionicons color={theme.colors.subtle} name="chevron-forward" size={16} />
          </View>
        ))}
      </CardBase>

      <Pressable onPress={() => undefined} style={styles.disclaimer}>
        <Ionicons color={theme.colors.primaryDark} name="shield-checkmark-outline" size={17} />
        <Text style={styles.disclaimerText}>健康数据用于日常记录与整理；如有不适或紧急情况，请联系医生或当地急救服务。</Text>
      </Pressable>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  briefCard: { backgroundColor: theme.colors.tealSoft },
  briefCopy: { flex: 1 },
  briefHeading: { alignItems: "center", flexDirection: "row", gap: 10, marginBottom: 14 },
  briefIcon: { alignItems: "center", backgroundColor: "#FFFFFF", borderRadius: theme.radius.pill, height: 40, justifyContent: "center", width: 40 },
  cardCaption: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 4 },
  cardTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" },
  detailLink: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  generatedAt: { color: theme.colors.subtle, fontSize: 11, marginTop: 10 },
  disclaimer: { alignItems: "flex-start", flexDirection: "row", gap: 8, paddingHorizontal: 4 },
  disclaimerText: { color: theme.colors.subtle, flex: 1, fontSize: 11, lineHeight: 17 },
  dotTeal: { backgroundColor: theme.colors.primary },
  metricGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10, marginTop: 14 },
  metricEntry: { alignItems: "center", alignSelf: "flex-start", flexDirection: "row", gap: 6, marginTop: 14 },
  metricEntryText: { color: theme.colors.primaryDark, fontSize: 13, fontWeight: "900" },
  overviewCard: { backgroundColor: "#FFFFFF" },
  overviewHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  recordDot: { backgroundColor: "#B9C9C3", borderRadius: 5, height: 8, width: 8 },
  recordCopy: { flex: 1 },
  recordDetail: { color: theme.colors.subtle, fontSize: 12, marginTop: 2 },
  recordRow: { alignItems: "center", borderTopColor: theme.colors.line, borderTopWidth: 1, flexDirection: "row", gap: 10, marginTop: 10, paddingTop: 10 },
  recordTitle: { color: theme.colors.ink, fontSize: 13, fontWeight: "800", lineHeight: 19 },
  resultBox: { backgroundColor: "#FFFFFF", borderRadius: theme.radius.sm, padding: 12 },
  resultText: { color: theme.colors.ink, fontSize: 13, lineHeight: 20 },
  sectionRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" }
});
