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
import type { ArchiveTrendSeries } from "@/types/api";

const metricInfo = {
  "blood-pressure": { average: "119/76", history: ["120/78 mmHg", "118/76 mmHg", "125/80 mmHg", "112/72 mmHg"], label: "血压历史", max: "132/84", min: "106/68", type: "blood_pressure", unit: "mmHg" },
  sleep: { average: "7.2", history: ["7.2 小时", "6.8 小时", "7.5 小时", "7.0 小时"], label: "睡眠历史", max: "8.1", min: "6.2", type: "sleep_duration", unit: "小时" },
  weight: { average: "62.1", history: ["62.1 kg", "62.4 kg", "62.0 kg", "62.3 kg"], label: "体重历史", max: "62.8", min: "61.7", type: "weight", unit: "kg" },
  steps: { average: "6,100", history: ["6,100 步", "5,820 步", "6,520 步", "5,760 步"], label: "步数历史", max: "7,420", min: "4,880", type: "steps", unit: "步" }
} as const;

function fallbackSeries(type: string, label: string, unit: string): ArchiveTrendSeries {
  const values = type === "steps" ? [6100, 5820, 6520, 5760, 7010, 6200] : type === "weight" ? [62.2, 62.4, 62.0, 62.1, 62.3, 62.1] : type === "sleep_duration" ? [6.8, 7.1, 7.3, 6.9, 7.4, 7.2] : [120, 118, 125, 112, 121, 119];
  return { count: values.length, data_quality: "demo", label, metric_type: type, points: values.map((value, index) => type === "blood_pressure" ? { diastolic: [78, 76, 80, 72, 77, 76][index], measured_at: `2026-07-${String(index + 5).padStart(2, "0")}`, systolic: value } : { measured_at: `2026-07-${String(index + 5).padStart(2, "0")}`, value }), summary: "系统内记录示例", unit };
}

export default function ArchiveMetricDetailScreen() {
  const { metric = "blood-pressure" } = useLocalSearchParams<{ metric: keyof typeof metricInfo }>();
  const info = metricInfo[metric] ?? metricInfo["blood-pressure"];
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const trends = useApiResource(() => provider.getArchiveTrends(), [session.currentUserId, session.dataMode]);
  const [period, setPeriod] = useState<Period>("全部");
  const series = trends.data?.series.find((item) => item.metric_type === info.type) ?? fallbackSeries(info.type, info.label.replace("历史", ""), info.unit);

  return (
    <AppScreen>
      <ArchiveSubHeader title={info.label} trailing="share" />
      <CardBase>
        <View style={styles.stats}>
          <View style={styles.stat}><Text style={styles.statLabel}>平均值</Text><Text style={styles.statValue}>{info.average}</Text><Text style={styles.unit}>{info.unit}</Text></View>
          <View style={styles.stat}><Text style={styles.statLabel}>最高值</Text><Text style={styles.statValue}>{info.max}</Text><Text style={styles.unit}>{info.unit}</Text></View>
          <View style={styles.stat}><Text style={styles.statLabel}>最低值</Text><Text style={styles.statValue}>{info.min}</Text><Text style={styles.unit}>{info.unit}</Text></View>
        </View>
        <Text style={styles.caption}>统计周期：系统内已有记录</Text>
      </CardBase>
      <PeriodSelector onChange={setPeriod} value={period} />
      {trends.error ? <ApiErrorState message={trends.error} /> : null}
      <CardBase><MetricHistoryChart series={series} /></CardBase>
      <ArchiveTimelineList items={info.history.map((detail, index) => ({ date: `2026-07-${String(10 - index * 3).padStart(2, "0")} 07:${String(30 - index * 5).padStart(2, "0")}`, detail, icon: "pulse-outline" as const, id: `${metric}-${index}`, title: info.label.replace("历史", "记录"), tone: theme.colors.primary }))} title="历史记录" />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  caption: { color: theme.colors.subtle, fontSize: 12, marginTop: 14 },
  stat: { flex: 1 },
  statLabel: { color: theme.colors.subtle, fontSize: 11, fontWeight: "700" },
  statValue: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 5 },
  stats: { flexDirection: "row", gap: 8 },
  unit: { color: theme.colors.subtle, fontSize: 11, marginTop: 3 }
});
