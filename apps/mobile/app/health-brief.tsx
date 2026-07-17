import { Ionicons } from "@expo/vector-icons";
import { useCallback, useMemo, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider, type PersonalArchiveRecentRecordsData } from "@/lib/dataProvider";
import type { BloodPressureRecord, HealthMetricRecord } from "@/types/api";

type MetricSummary = {
  average: string | null;
  count: number;
  label: string;
  latestAt: string;
  latestValue: string;
};

type SummarySection = {
  color: string;
  icon: keyof typeof Ionicons.glyphMap;
  id: string;
  metrics: MetricSummary[];
  title: string;
};

function formatGeneratedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  return date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" });
}

function formatRecordTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "时间待补充";
  return date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" });
}

function recentSevenDays<T extends { measured_at?: string; recorded_at?: string }>(records: T[]): T[] {
  const start = new Date();
  start.setDate(start.getDate() - 7);
  return records.filter((record) => new Date(record.measured_at ?? record.recorded_at ?? 0).getTime() >= start.getTime());
}

function latest<T extends { measured_at?: string; recorded_at?: string }>(records: T[]): T | null {
  return [...records].sort((left, right) => new Date(right.measured_at ?? right.recorded_at ?? 0).getTime() - new Date(left.measured_at ?? left.recorded_at ?? 0).getTime())[0] ?? null;
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(/\.0$/, "");
}

function formatMetricValue(record: HealthMetricRecord): string {
  const value = record.value_numeric;
  if (value === undefined || value === null) return record.value_text?.trim() || "已记录";
  if (record.metric_type === "sleep_duration") {
    const hours = Math.floor(value);
    const minutes = Math.round((value - hours) * 60);
    return `${hours}小时${minutes ? `${minutes}分钟` : ""}`;
  }
  const unit = record.metric_type === "heart_rate" ? "次/分" : record.metric_type === "steps" ? "步" : record.unit ?? "";
  return `${formatNumber(value)}${unit ? ` ${unit}` : ""}`;
}

function summaryForMetric(records: HealthMetricRecord[], metricType: string, label: string): MetricSummary | null {
  const inRange = recentSevenDays(records.filter((record) => record.metric_type === metricType));
  const latestRecord = latest(inRange);
  if (!latestRecord) return null;
  const numeric = inRange.map((record) => record.value_numeric).filter((value): value is number => typeof value === "number");
  const average = numeric.length
    ? formatMetricValue({ ...latestRecord, value_numeric: numeric.reduce((sum, value) => sum + value, 0) / numeric.length })
    : null;
  return { average, count: inRange.length, label, latestAt: latestRecord.measured_at, latestValue: formatMetricValue(latestRecord) };
}

function summaryForBloodPressure(records: BloodPressureRecord[]): MetricSummary | null {
  const inRange = recentSevenDays(records);
  const latestRecord = latest(inRange);
  if (!latestRecord) return null;
  const systolicAverage = Math.round(inRange.reduce((sum, record) => sum + record.systolic, 0) / inRange.length);
  const diastolicAverage = Math.round(inRange.reduce((sum, record) => sum + record.diastolic, 0) / inRange.length);
  return {
    average: `${systolicAverage}/${diastolicAverage} mmHg`,
    count: inRange.length,
    label: "血压",
    latestAt: latestRecord.recorded_at,
    latestValue: `${latestRecord.systolic}/${latestRecord.diastolic} mmHg`
  };
}

function buildSections(data: PersonalArchiveRecentRecordsData | null): SummarySection[] {
  const metrics = data?.metrics ?? [];
  const bloodPressure = summaryForBloodPressure(data?.bloodPressure ?? []);
  const body = [bloodPressure, summaryForMetric(metrics, "weight", "体重"), summaryForMetric(metrics, "heart_rate", "心率"), summaryForMetric(metrics, "temperature", "体温")].filter((item): item is MetricSummary => Boolean(item));
  const lifestyle = [summaryForMetric(metrics, "sleep_duration", "睡眠")].filter((item): item is MetricSummary => Boolean(item));
  const habits = [summaryForMetric(metrics, "steps", "步数")].filter((item): item is MetricSummary => Boolean(item));
  const sections: SummarySection[] = [
    { color: "#E86962", icon: "heart", id: "body", metrics: body, title: "身体指标" },
    { color: "#5B89E8", icon: "moon", id: "lifestyle", metrics: lifestyle, title: "生活状态" },
    { color: "#23B99B", icon: "footsteps", id: "habits", metrics: habits, title: "日常习惯" }
  ];
  return sections.filter((section) => section.metrics.length > 0);
}

function extractBriefSection(content: string | null, heading: string): string | null {
  if (!content) return null;
  const lines = content.split("\n").map((line) => line.trim());
  const sectionIndex = lines.findIndex((line) => line.includes(heading));
  if (sectionIndex < 0) return null;
  const nextHeading = lines.slice(sectionIndex + 1).findIndex((line) => /^(❤️|😴|🏃|💡|📌)/.test(line));
  const sectionLines = lines.slice(sectionIndex + 1, nextHeading < 0 ? undefined : sectionIndex + 1 + nextHeading);
  const value = sectionLines.filter((line) => line && !line.includes("不替代医生判断")).join("\n");
  return value || null;
}

function MetricCard({ item }: { item: MetricSummary }) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricLabel}>{item.label}</Text>
      <View style={styles.dataRow}>
        <Text style={styles.dataLabel}>最近一次记录：</Text>
        <Text style={styles.dataTime}>{formatRecordTime(item.latestAt)}</Text>
        <Text style={styles.dataValue}>{item.latestValue}</Text>
      </View>
      <View style={styles.dataRow}>
        <Text style={styles.dataLabel}>{item.count > 1 ? "近 7 天平均：" : "近 7 天记录："}</Text>
        <Text style={styles.averageValue}>{item.count > 1 ? item.average ?? "—" : "—"}</Text>
        <Text style={styles.count}>共 {item.count} 次</Text>
      </View>
    </View>
  );
}

export default function HealthBriefScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const latest = useApiResource(() => provider.getLatestDailyHealthBrief(), [session.currentUserId, session.dataMode]);
  const archive = useApiResource(() => provider.getPersonalArchiveRecentRecords(), [session.currentUserId, session.dataMode]);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const content = latest.data?.generated_content ?? null;
  const sections = useMemo(() => buildSections(archive.data), [archive.data]);
  const suggestion = extractBriefSection(content, "健康建议");
  const reminder = extractBriefSection(content, "小提醒");

  const refreshBrief = useCallback(async () => {
    setRefreshing(true);
    setRefreshError(null);
    const result = await provider.runDailyHealthBrief(session.currentUserId);
    setRefreshing(false);
    if (!result.ok) {
      setRefreshError(result.error?.message ?? "健康小结暂时无法整理，请稍后再试。");
      return;
    }
    await Promise.all([latest.reload(), archive.reload()]);
  }, [archive.reload, latest.reload, provider, session.currentUserId]);

  return (
    <AppScreen>
      <ArchiveSubHeader title="健康小结" />
      <CardBase style={styles.heroCard}>
        <View style={styles.heroIcon}><Ionicons color={theme.colors.primaryDark} name="sparkles-outline" size={22} /></View>
        <View style={styles.heroCopy}>
          <Text style={styles.title}>健康小结 🌱</Text>
          <Text style={styles.subtitle}>最近 7 天已记录信息整理</Text>
        </View>
        {content ? <Text style={styles.generatedAt}>生成于{formatGeneratedAt(latest.data?.generated_at ?? "")}</Text> : null}
      </CardBase>

      {latest.loading || archive.loading ? <Text style={styles.loading}>正在读取健康小结与档案记录...</Text> : null}
      {latest.error ? <ApiErrorState message={latest.error} /> : null}
      {archive.error ? <ApiErrorState message={archive.error} /> : null}
      {refreshError ? <ApiErrorState message={refreshError} /> : null}

      {content && suggestion ? (
        <CardBase style={styles.suggestionCard}>
          <View style={styles.sectionHeading}>
            <View style={styles.suggestionIcon}><Ionicons color="#268C78" name="leaf-outline" size={18} /></View>
            <Text style={styles.sectionTitle}>健康建议</Text>
          </View>
          <Text style={styles.suggestionIntro}>根据本次健康小结生成</Text>
          <View style={styles.suggestionRow}>
            <Ionicons color="#268C78" name="bulb-outline" size={17} />
            <Text style={styles.suggestionText}>{suggestion}</Text>
          </View>
        </CardBase>
      ) : null}

      {content && sections.map((section) => (
        <CardBase key={section.id} style={styles.sectionCard}>
          <View style={styles.sectionHeading}>
            <View style={[styles.sectionIcon, { backgroundColor: `${section.color}18` }]}><Ionicons color={section.color} name={section.icon} size={18} /></View>
            <Text style={styles.sectionTitle}>{section.title}</Text>
          </View>
          {section.metrics.map((item) => <MetricCard key={item.label} item={item} />)}
        </CardBase>
      ))}

      {content && reminder ? (
        <CardBase style={styles.reminderCard}>
          <View style={styles.sectionHeading}><Ionicons color="#D58036" name="pin-outline" size={19} /><Text style={styles.sectionTitle}>小提醒</Text></View>
          <Text style={styles.reminderText}>{reminder}</Text>
        </CardBase>
      ) : null}

      {content && !archive.loading && sections.length === 0 ? <CardBase style={styles.emptyCard}><Text style={styles.emptyTitle}>本次小结暂无可展示的指标</Text><Text style={styles.emptyText}>系统内暂时没有最近 7 天的正式指标记录。</Text></CardBase> : null}
      {!content && !latest.loading ? <CardBase style={styles.emptyCard}><Text style={styles.emptyTitle}>还没有健康小结</Text><Text style={styles.emptyText}>生成后会在这里以卡片展示最近的正式健康记录。</Text></CardBase> : null}

      {content ? <Text style={styles.safetyText}>基于系统内已有记录整理，不替代医生判断；如有明显不适请及时就医。</Text> : null}
      <PrimaryButton disabled={refreshing} label={refreshing ? "正在更新..." : content ? "更新个人健康小结" : "生成个人健康小结"} onPress={refreshBrief} />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  averageValue: { color: theme.colors.ink, fontSize: 13, fontWeight: "800" },
  count: { color: theme.colors.subtle, fontSize: 12, marginLeft: "auto" },
  dataLabel: { color: theme.colors.subtle, fontSize: 12 },
  dataRow: { alignItems: "center", flexDirection: "row", gap: 4, marginTop: 7 },
  dataTime: { color: theme.colors.subtle, fontSize: 12 },
  dataValue: { color: theme.colors.ink, fontSize: 13, fontWeight: "900", marginLeft: "auto" },
  emptyCard: { backgroundColor: theme.colors.tealSoft, gap: 7 },
  emptyText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19 },
  emptyTitle: { color: theme.colors.primaryDark, fontSize: 16, fontWeight: "900" },
  generatedAt: { color: theme.colors.subtle, fontSize: 11, marginTop: 2 },
  heroCard: { alignItems: "center", backgroundColor: theme.colors.tealSoft, flexDirection: "row", gap: 10, paddingVertical: 14 },
  heroCopy: { flex: 1 },
  heroIcon: { alignItems: "center", backgroundColor: "#FFFFFF", borderRadius: 20, height: 40, justifyContent: "center", width: 40 },
  loading: { color: theme.colors.subtle, fontSize: 13 },
  metricCard: { backgroundColor: "#F8FBFA", borderRadius: theme.radius.sm, marginTop: 9, padding: 11 },
  metricLabel: { color: theme.colors.ink, fontSize: 14, fontWeight: "900" },
  reminderCard: { backgroundColor: "#FFF8EB", gap: 8 },
  reminderText: { color: theme.colors.ink, fontSize: 13, lineHeight: 20 },
  safetyText: { color: theme.colors.subtle, fontSize: 11, lineHeight: 17, paddingHorizontal: 4 },
  sectionCard: { gap: 3 },
  sectionHeading: { alignItems: "center", flexDirection: "row", gap: 8 },
  sectionIcon: { alignItems: "center", borderRadius: 14, height: 28, justifyContent: "center", width: 28 },
  sectionTitle: { color: theme.colors.ink, fontSize: 16, fontWeight: "900" },
  suggestionCard: { backgroundColor: "#F2FBF7", gap: 9 },
  suggestionIcon: { alignItems: "center", backgroundColor: "#DDF5EA", borderRadius: 14, height: 28, justifyContent: "center", width: 28 },
  suggestionIntro: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18 },
  suggestionRow: { alignItems: "flex-start", flexDirection: "row", gap: 8 },
  suggestionText: { color: theme.colors.ink, flex: 1, fontSize: 13, lineHeight: 20 },
  subtitle: { color: theme.colors.subtle, fontSize: 12, marginTop: 3 },
  title: { color: theme.colors.ink, fontSize: 19, fontWeight: "900" }
});
