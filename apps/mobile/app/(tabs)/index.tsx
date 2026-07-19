import { Ionicons } from "@expo/vector-icons";
import { Link, router } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useFocusEffect } from "@react-navigation/native";
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
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider, type PersonalArchiveRecentRecordsData } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse, BloodPressureRecord, HealthMetricRecord } from "@/types/api";

type HomeMetricTile = {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  note: string;
  tone: "blue" | "coral" | "lavender" | "teal";
  value: string;
  wide?: boolean;
};

type HomeRecentRecord = {
  detail: string;
  icon: keyof typeof Ionicons.glyphMap;
  id: string;
  measuredAt: string;
  tone: string;
  title: string;
};

const personalBriefFallback = "尚未生成健康小结。生成后可在详情页查看最近 7 天的记录整理。";

function formatGeneratedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "刚刚";
  }
  return date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" });
}

function formatRecordedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "记录时间待补充";
  return `记录时间：${date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" })}`;
}

function formatMetricValue(metric: HealthMetricRecord): string {
  const value = metric.value_numeric;
  if (value === null || value === undefined) return metric.value_text?.trim() || "已记录";
  if (metric.metric_type === "sleep_duration") {
    const hours = Math.floor(value);
    const minutes = Math.round((value - hours) * 60);
    return `${hours} 小时${minutes ? ` ${minutes} 分钟` : ""}`;
  }
  const unit = metric.metric_type === "heart_rate" ? "次/分" : metric.metric_type === "steps" ? "步" : metric.unit ?? "";
  return `${value}${unit ? ` ${unit}` : ""}`;
}

function metricLabel(metricType: string): string {
  return ({ heart_rate: "心率", sleep_duration: "睡眠", steps: "步数", temperature: "体温", weight: "体重" } as Record<string, string>)[metricType] ?? "健康指标";
}

function metricRecordIcon(metricType: string): keyof typeof Ionicons.glyphMap {
  return ({
    heart_rate: "heart-outline",
    sleep_duration: "moon-outline",
    steps: "footsteps-outline",
    temperature: "thermometer-outline",
    weight: "scale-outline"
  } as Record<string, keyof typeof Ionicons.glyphMap>)[metricType] ?? "analytics-outline";
}

function formatLatestMetricTime(value: string | null | undefined): string {
  if (!value) return "暂无已记录";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "时间待补充";
  return `最近一次：${date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" })}`;
}

function newest<T extends { measured_at?: string; recorded_at?: string }>(records: T[]): T | null {
  return [...records].sort((left, right) => new Date(right.measured_at ?? right.recorded_at ?? 0).getTime() - new Date(left.measured_at ?? left.recorded_at ?? 0).getTime())[0] ?? null;
}

function buildHomeMetrics(bloodPressure: BloodPressureRecord[], records: HealthMetricRecord[]): HomeMetricTile[] {
  const latestByType = (type: string) => newest(records.filter((record) => record.metric_type === type));
  const latestBloodPressure = newest(bloodPressure);
  const metricTile = (type: string, icon: HomeMetricTile["icon"], tone: HomeMetricTile["tone"], wide = false): HomeMetricTile => {
    const latest = latestByType(type);
    return { icon, label: metricLabel(type), note: formatLatestMetricTime(latest?.measured_at), tone, value: latest ? formatMetricValue(latest) : "--", wide };
  };
  return [
    metricTile("sleep_duration", "moon-outline", "blue"),
    metricTile("steps", "footsteps-outline", "teal"),
    metricTile("heart_rate", "heart-outline", "coral"),
    { icon: "pulse-outline", label: "血压", note: formatLatestMetricTime(latestBloodPressure?.recorded_at), tone: "lavender", value: latestBloodPressure ? `${latestBloodPressure.systolic}/${latestBloodPressure.diastolic}` : "--" },
    metricTile("weight", "scale-outline", "teal", true)
  ];
}

function buildRecentRecords(data: PersonalArchiveRecentRecordsData | null): HomeRecentRecord[] {
  if (!data) return [];
  const metricRecords = data.metrics.map((record) => ({ detail: formatMetricValue(record), icon: metricRecordIcon(record.metric_type), id: record.id, measuredAt: record.measured_at, title: `${metricLabel(record.metric_type)}记录`, tone: theme.colors.primary }));
  const bloodPressureRecords = data.bloodPressure.map((record) => ({ detail: `${record.systolic}/${record.diastolic} mmHg`, icon: "pulse-outline" as const, id: record.id, measuredAt: record.recorded_at, title: "血压记录", tone: "#8168D8" }));
  const symptomRecords = data.symptoms.map((record) => ({ detail: record.summary, icon: "heart-outline" as const, id: record.id, measuredAt: record.recorded_at, title: record.title || "症状记录", tone: "#F38A69" }));
  return [...metricRecords, ...bloodPressureRecords, ...symptomRecords]
    .sort((left, right) => new Date(right.measuredAt).getTime() - new Date(left.measuredAt).getTime())
    .slice(0, 4);
}

export default function HomeScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [brief, setBrief] = useState<AgentRunResponse | null>(null);
  const [briefGeneratedAt, setBriefGeneratedAt] = useState<string | null>(null);
  const [briefError, setBriefError] = useState<string | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const trendResource = useApiResource(() => provider.getArchiveTrends(), [session.currentUserId]);
  const timelineResource = useApiResource(() => provider.getPersonalArchiveRecentRecords(), [session.currentUserId, session.dataMode]);
  const homeMetrics = useMemo(() => buildHomeMetrics(timelineResource.data?.bloodPressure ?? [], timelineResource.data?.metrics ?? []), [timelineResource.data]);
  const recentRecords = useMemo(() => buildRecentRecords(timelineResource.data), [timelineResource.data]);

  useFocusEffect(useCallback(() => {
    void trendResource.reload();
    void timelineResource.reload();
  }, [timelineResource.reload, trendResource.reload]));

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
        title={`早上好，${session.authSession.user?.nickname ?? ""}`.trim()}
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
          {homeMetrics.map((metric) => (
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
            <Text style={styles.cardCaption}>近期系统内记录整理</Text>
          </View>
        </View>
        <View style={styles.resultBox}>
          <Text style={styles.generatedAt}>{briefGeneratedAt ? `最近生成：${formatGeneratedAt(briefGeneratedAt)}` : "尚未生成健康小结"}</Text>
          <Pressable accessibilityRole="button" disabled={!brief} onPress={() => router.push(routes.healthBrief)} style={[styles.briefDetailLink, !brief ? styles.briefDetailLinkDisabled : null]}>
            <Text style={[styles.briefDetailText, !brief ? styles.briefDetailTextDisabled : null]}>查看健康小结详情</Text>
            <Ionicons color={brief ? theme.colors.primaryDark : theme.colors.subtle} name="chevron-forward" size={17} />
          </Pressable>
          {!brief ? <Text style={styles.briefHint}>{personalBriefFallback}</Text> : null}
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
        {recentRecords.length ? recentRecords.map((record) => (
          <Pressable key={record.id} onPress={() => router.push(routes.archive)} style={styles.recordRow}>
            <View style={[styles.recordIcon, { backgroundColor: `${record.tone}16` }]}>
              <Ionicons color={record.tone} name={record.icon} size={16} />
            </View>
            <View style={styles.recordCopy}>
              <Text style={styles.recordTitle}>{record.title}</Text>
              <Text style={styles.recordDetail}>{record.detail}</Text>
              <Text style={styles.recordTime}>{formatRecordedAt(record.measuredAt)}</Text>
            </View>
            <Ionicons color={theme.colors.subtle} name="chevron-forward" size={16} />
          </Pressable>
        )) : <Text style={styles.emptyRecords}>系统内暂无健康指标记录。</Text>}
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
  briefDetailLink: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", minHeight: 34 },
  briefDetailLinkDisabled: { opacity: 0.58 },
  briefDetailText: { color: theme.colors.primaryDark, fontSize: 14, fontWeight: "900" },
  briefDetailTextDisabled: { color: theme.colors.subtle },
  briefHint: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 6 },
  briefCopy: { flex: 1 },
  briefHeading: { alignItems: "center", flexDirection: "row", gap: 10, marginBottom: 14 },
  briefIcon: { alignItems: "center", backgroundColor: "#FFFFFF", borderRadius: theme.radius.pill, height: 40, justifyContent: "center", width: 40 },
  cardCaption: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 4 },
  cardTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" },
  detailLink: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  generatedAt: { color: theme.colors.subtle, fontSize: 11, marginBottom: 8 },
  disclaimer: { alignItems: "flex-start", flexDirection: "row", gap: 8, paddingHorizontal: 4 },
  disclaimerText: { color: theme.colors.subtle, flex: 1, fontSize: 11, lineHeight: 17 },
  emptyRecords: { color: theme.colors.subtle, fontSize: 13, paddingTop: 10 },
  metricGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10, marginTop: 14 },
  metricEntry: { alignItems: "center", alignSelf: "flex-start", flexDirection: "row", gap: 6, marginTop: 14 },
  metricEntryText: { color: theme.colors.primaryDark, fontSize: 13, fontWeight: "900" },
  overviewCard: { backgroundColor: "#FFFFFF" },
  overviewHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  recordIcon: { alignItems: "center", borderRadius: 10, height: 32, justifyContent: "center", width: 32 },
  recordCopy: { flex: 1 },
  recordDetail: { color: theme.colors.subtle, fontSize: 12, marginTop: 2 },
  recordTime: { color: theme.colors.subtle, fontSize: 11, marginTop: 3 },
  recordRow: { alignItems: "center", borderTopColor: theme.colors.line, borderTopWidth: 1, flexDirection: "row", gap: 10, marginTop: 10, paddingTop: 10 },
  recordTitle: { color: theme.colors.ink, fontSize: 13, fontWeight: "800", lineHeight: 19 },
  resultBox: { backgroundColor: "#FFFFFF", borderRadius: theme.radius.sm, padding: 12 },
  sectionRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" }
});
