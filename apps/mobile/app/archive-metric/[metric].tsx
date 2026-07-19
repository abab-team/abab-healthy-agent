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
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { ArchiveTrendPoint, ArchiveTrendSeries } from "@/types/api";

const metricInfo: Record<string, { label: string; type: string; unit: string }> = {
  "blood-pressure": { label: "血压", type: "blood_pressure", unit: "mmHg" },
  sleep: { label: "睡眠", type: "sleep_duration", unit: "小时" },
  weight: { label: "体重", type: "weight", unit: "kg" },
  steps: { label: "步数", type: "steps", unit: "步" },
  "heart-rate": { label: "心率", type: "heart_rate", unit: "次/分" },
  temperature: { label: "体温", type: "temperature", unit: "°C" }
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
    const pair = kind === "average"
      ? [Math.round(systolic.reduce((sum, value) => sum + value, 0) / systolic.length), Math.round(diastolic.reduce((sum, value) => sum + value, 0) / diastolic.length)]
      : kind === "max" ? [Math.max(...systolic), Math.max(...diastolic)] : [Math.min(...systolic), Math.min(...diastolic)];
    return `${pair[0]}/${pair[1]}`;
  }
  const value = kind === "average" ? values.reduce((sum, item) => sum + item, 0) / values.length : kind === "max" ? Math.max(...values) : Math.min(...values);
  return value < 10 ? value.toFixed(1) : Math.round(value).toLocaleString("zh-CN");
}

function pointDetail(point: ArchiveTrendPoint, series: ArchiveTrendSeries): string {
  if (series.metric_type === "blood_pressure") return `${point.systolic ?? "--"}/${point.diastolic ?? "--"} mmHg`;
  const value = point.value;
  if (value === null || value === undefined) return "已记录";
  if (series.metric_type === "sleep_duration") {
    const hours = Math.floor(value);
    const minutes = Math.round((value - hours) * 60);
    return `${hours} 小时${minutes ? ` ${minutes} 分钟` : ""}`;
  }
  return `${value.toLocaleString("zh-CN")} ${series.unit ?? ""}`.trim();
}

export default function ArchiveMetricDetailScreen() {
  const { metric = "blood-pressure" } = useLocalSearchParams<{ metric: string }>();
  const info = metricInfo[metric] ?? metricInfo["blood-pressure"];
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const trends = useApiResource(() => provider.getArchiveTrends(), [session.currentUserId, session.dataMode]);
  const [period, setPeriod] = useState<Period>("全部");
  const series = trends.data?.series.find((item) => item.metric_type === info.type) ?? {
    count: 0,
    data_quality: "system",
    label: info.label,
    metric_type: info.type,
    points: [],
    summary: "系统内暂无记录",
    unit: info.unit
  };
  const history = [...series.points].reverse().map((point, index) => ({
    date: point.measured_at.replace("T", " ").slice(0, 16),
    detail: pointDetail(point, series),
    icon: "pulse-outline" as const,
    id: `${info.type}-${point.measured_at}-${index}`,
    title: `${info.label}记录`,
    tone: theme.colors.primary
  }));

  return (
    <AppScreen>
      <ArchiveSubHeader title={`${info.label}历史`} trailing="share" />
      {trends.error ? <ApiErrorState message={trends.error} /> : null}
      <CardBase>
        <View style={styles.stats}>
          <View style={styles.stat}><Text style={styles.statLabel}>平均值</Text><Text style={styles.statValue}>{statText(series, "average")}</Text><Text style={styles.unit}>{info.unit}</Text></View>
          <View style={styles.stat}><Text style={styles.statLabel}>最高值</Text><Text style={styles.statValue}>{statText(series, "max")}</Text><Text style={styles.unit}>{info.unit}</Text></View>
          <View style={styles.stat}><Text style={styles.statLabel}>最低值</Text><Text style={styles.statValue}>{statText(series, "min")}</Text><Text style={styles.unit}>{info.unit}</Text></View>
        </View>
        <Text style={styles.caption}>统计周期：系统内已有记录</Text>
      </CardBase>
      <PeriodSelector onChange={setPeriod} value={period} />
      <CardBase><MetricHistoryChart series={series} /></CardBase>
      {history.length ? <ArchiveTimelineList items={history} title="历史记录" /> : <CardBase><Text style={styles.empty}>系统内暂无{info.label}记录。</Text></CardBase>}
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  caption: { color: theme.colors.subtle, fontSize: 12, marginTop: 14 },
  empty: { color: theme.colors.subtle, fontSize: 14, textAlign: "center" },
  stat: { flex: 1 },
  statLabel: { color: theme.colors.subtle, fontSize: 11, fontWeight: "700" },
  statValue: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 5 },
  stats: { flexDirection: "row", gap: 8 },
  unit: { color: theme.colors.subtle, fontSize: 11, marginTop: 3 }
});
