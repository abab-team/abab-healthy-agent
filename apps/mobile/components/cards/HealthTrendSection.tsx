import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { TrendCard } from "@/components/cards/TrendCard";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { Period, PeriodSelector } from "@/components/common/PeriodSelector";
import { theme } from "@/constants/theme";
import type { ArchiveTrendSeries, ArchiveTrends } from "@/types/api";

type HealthTrendSectionProps = {
  trends: ArchiveTrends | null;
  loading: boolean;
  error: string | null;
};

function preferredSeries(trends: ArchiveTrends | null): ArchiveTrendSeries[] {
  return ["sleep_duration", "blood_pressure", "weight"]
    .map((metricType) => trends?.series.find((series) => series.metric_type === metricType))
    .filter((series): series is ArchiveTrendSeries => Boolean(series));
}

export function HealthTrendSection({ trends, loading, error }: HealthTrendSectionProps) {
  const [period, setPeriod] = useState<Period>("30天");
  const series = preferredSeries(trends);

  return (
    <CardBase style={styles.section}>
      <View style={styles.heading}>
        <View>
          <Text style={styles.title}>长期趋势</Text>
          <Text style={styles.caption}>基于系统内已有记录整理，不作医学判断。</Text>
        </View>
        {loading ? <Text style={styles.loading}>加载中</Text> : null}
      </View>
      <PeriodSelector onChange={setPeriod} value={period} />
      {error ? <ApiErrorState message={error} /> : null}
      <View style={styles.cards}>
        {series.map((item) => <TrendCard key={item.metric_type} series={item} />)}
      </View>
      {!loading && !error && series.length === 0 ? <Text style={styles.empty}>系统内暂无趋势记录。</Text> : null}
    </CardBase>
  );
}

const styles = StyleSheet.create({
  caption: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 4 },
  cards: { gap: 10, marginTop: 2 },
  empty: { color: theme.colors.subtle, fontSize: 13, paddingVertical: 10 },
  heading: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  loading: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "800" },
  section: { gap: 14 },
  title: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" }
});
