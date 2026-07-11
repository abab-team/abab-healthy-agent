import { useLocalSearchParams } from "expo-router";
import { useMemo, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { ArchiveTimelineList } from "@/components/cards/ArchiveTimelineList";
import { CardBase } from "@/components/cards/CardBase";
import { MetricHistoryChart } from "@/components/cards/MetricHistoryChart";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { Period, PeriodSelector } from "@/components/common/PeriodSelector";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { members as mockMembers } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { ArchiveTrendSeries } from "@/types/api";

const labels: Record<string, { label: string; metricType: string; unit: string }> = {
  "blood-pressure": { label: "血压", metricType: "blood_pressure", unit: "mmHg" },
  sleep: { label: "睡眠", metricType: "sleep_duration", unit: "小时" },
  weight: { label: "体重", metricType: "weight", unit: "kg" },
  steps: { label: "步数", metricType: "steps", unit: "步" }
};

function valuesFor(series: ArchiveTrendSeries) {
  return series.points.map((point) => series.metric_type === "blood_pressure" ? point.systolic ?? 0 : point.value ?? 0).filter((value) => value > 0);
}

function statText(series: ArchiveTrendSeries, kind: "average" | "max" | "min") {
  const values = valuesFor(series);
  if (!values.length) return "--";
  if (series.metric_type === "blood_pressure") {
    const systolic = series.points.map((point) => point.systolic ?? 0).filter(Boolean);
    const diastolic = series.points.map((point) => point.diastolic ?? 0).filter(Boolean);
    const pair = kind === "average" ? [Math.round(systolic.reduce((sum, value) => sum + value, 0) / systolic.length), Math.round(diastolic.reduce((sum, value) => sum + value, 0) / diastolic.length)] : kind === "max" ? [Math.max(...systolic), Math.max(...diastolic)] : [Math.min(...systolic), Math.min(...diastolic)];
    return `${pair[0]}/${pair[1]}`;
  }
  const value = kind === "average" ? values.reduce((sum, item) => sum + item, 0) / values.length : kind === "max" ? Math.max(...values) : Math.min(...values);
  return value < 10 ? value.toFixed(1) : Math.round(value).toLocaleString("zh-CN");
}

export default function MemberMetricDetailScreen() {
  const { id, metric = "blood-pressure" } = useLocalSearchParams<{ id: string; metric: string }>();
  const info = labels[metric] ?? labels["blood-pressure"];
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const resource = useApiResource(() => provider.getMemberArchiveSection(String(id), "metrics"), [id, session.currentUserId, session.dataMode]);
  const [period, setPeriod] = useState<Period>("全部");
  const member = resource.data?.member;
  const isSelf = member?.user_id === session.currentUserId || String(id) === session.currentUserId;
  const mockMember = mockMembers.find((item) => item.id === id) ?? mockMembers[0];
  const denied = resource.errorCode === "permission_denied" || resource.errorCode === "forbidden";
  const points = metric === "blood-pressure" ? (resource.data?.bloodPressure ?? []).map((item) => ({ diastolic: item.diastolic, measured_at: item.recorded_at, systolic: item.systolic })) : (resource.data?.metrics ?? []).filter((item) => metric === "sleep" ? ["sleep", "sleep_duration"].includes(item.metric_type) : item.metric_type === info.metricType).map((item) => ({ measured_at: item.measured_at, value: item.value_numeric ?? 0 }));
  const series: ArchiveTrendSeries = { count: points.length, data_quality: "shared", label: info.label, metric_type: info.metricType, points, summary: "成员已共享的系统内记录", unit: info.unit };
  const history = points.map((point, index) => ({ date: point.measured_at.replace("T", " ").slice(0, 16), detail: "systolic" in point ? `${point.systolic}/${point.diastolic} mmHg` : `${point.value} ${info.unit}`, icon: "pulse-outline" as const, id: `${metric}-${index}`, title: `${info.label}记录`, tone: theme.colors.primary }));

  return <AppScreen><ArchiveSubHeader title={isSelf ? `我的${info.label}历史` : `${member?.display_name ?? mockMember.name}的${info.label}历史`} />{resource.loading ? <Text style={styles.loading}>正在读取成员共享资料…</Text> : null}{denied ? <CardBase><Text style={styles.denied}>暂无查看权限</Text></CardBase> : null}{resource.error && !denied ? <ApiErrorState message={resource.error} /> : null}{resource.data ? <><CardBase><View style={styles.stats}><View style={styles.stat}><Text style={styles.statLabel}>平均值</Text><Text style={styles.statValue}>{statText(series, "average")}</Text><Text style={styles.unit}>{info.unit}</Text></View><View style={styles.stat}><Text style={styles.statLabel}>最高值</Text><Text style={styles.statValue}>{statText(series, "max")}</Text><Text style={styles.unit}>{info.unit}</Text></View><View style={styles.stat}><Text style={styles.statLabel}>最低值</Text><Text style={styles.statValue}>{statText(series, "min")}</Text><Text style={styles.unit}>{info.unit}</Text></View></View><Text style={styles.caption}>统计周期：{isSelf ? "系统内已有记录" : "成员已共享的系统内记录"}</Text></CardBase><PeriodSelector onChange={setPeriod} value={period} /><CardBase><MetricHistoryChart series={series} /></CardBase>{history.length ? <ArchiveTimelineList items={history} title="历史记录" /> : <CardBase><Text style={styles.empty}>系统内暂无可展示的已共享记录。</Text></CardBase>}</> : null}</AppScreen>;
}

const styles = StyleSheet.create({
  caption: { color: theme.colors.subtle, fontSize: 12, marginTop: 14 },
  denied: { color: theme.colors.ink, fontSize: 17, fontWeight: "900" },
  empty: { color: theme.colors.subtle, fontSize: 14, textAlign: "center" },
  loading: { color: theme.colors.subtle, fontSize: 13 },
  stat: { flex: 1 },
  statLabel: { color: theme.colors.subtle, fontSize: 11, fontWeight: "700" },
  statValue: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 5 },
  stats: { flexDirection: "row", gap: 8 },
  unit: { color: theme.colors.subtle, fontSize: 11, marginTop: 3 }
});
