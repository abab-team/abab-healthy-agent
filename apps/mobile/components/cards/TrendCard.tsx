import { useMemo, useState } from "react";
import { LayoutChangeEvent, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";
import type { ArchiveTrendSeries } from "@/types/api";

type ChartPoint = { label: string; value: number };

function chartPoints(series: ArchiveTrendSeries): ChartPoint[] {
  return series.points.slice(-7).map((point) => ({
    label: point.measured_at.slice(5, 10).replace("-", "/"),
    value: typeof point.value === "number" ? point.value : point.systolic ?? 0
  }));
}

function averageLabel(series: ArchiveTrendSeries, points: ChartPoint[]): string {
  if (points.length === 0) return "系统内暂无记录";
  if (series.metric_type === "blood_pressure") {
    const systolic = series.points.reduce((total, point) => total + (point.systolic ?? 0), 0) / series.points.length;
    const diastolic = series.points.reduce((total, point) => total + (point.diastolic ?? 0), 0) / series.points.length;
    return `${Math.round(systolic)}/${Math.round(diastolic)} mmHg`;
  }
  const average = points.reduce((total, point) => total + point.value, 0) / points.length;
  const rounded = Math.abs(average) < 10 ? average.toFixed(1) : Math.round(average).toLocaleString("zh-CN");
  const unit = series.unit === "hours" ? "小时" : series.unit === "steps" ? "步" : series.unit ?? "";
  return `${rounded}${unit ? ` ${unit}` : ""}`;
}

function changeLabel(series: ArchiveTrendSeries, points: ChartPoint[]): string {
  if (points.length < 2) return "记录不足以比较变化";
  const change = points[points.length - 1].value - points[0].value;
  const display = Math.abs(change) < 10 ? change.toFixed(1) : Math.round(change).toString();
  const unit = series.unit === "hours" ? "小时" : series.unit === "steps" ? "步" : series.unit ?? "";
  return `较上周期 ${change >= 0 ? "+" : ""}${display}${unit ? ` ${unit}` : ""}`;
}

function MiniLineChart({ points, tone }: { points: ChartPoint[]; tone: string }) {
  const [width, setWidth] = useState(0);
  const chartHeight = 54;
  const values = points.map((point) => point.value);
  const rawMinimum = Math.min(...values);
  const rawMaximum = Math.max(...values);
  const span = Math.max(rawMaximum - rawMinimum, Math.abs(rawMaximum) * 0.08, 1);
  const padding = span * 0.18;
  const minimum = rawMinimum - padding;
  const maximum = rawMaximum + padding;
  const positions = points.map((point, index) => ({
    left: points.length === 1 ? width / 2 : 4 + (index / (points.length - 1)) * Math.max(width - 8, 0),
    top: chartHeight - 8 - ((point.value - minimum) / span) * (chartHeight - 18)
  }));

  const yTicks = [maximum, (maximum + minimum) / 2, minimum];

  return (
    <View style={styles.chartRow}>
      <View style={styles.yAxis}>{yTicks.map((tick) => <Text key={tick} style={styles.yAxisLabel}>{Math.abs(tick) < 10 ? tick.toFixed(1) : Math.round(tick)}</Text>)}</View>
      <View onLayout={(event: LayoutChangeEvent) => setWidth(event.nativeEvent.layout.width)} style={styles.chart}>
      <View style={[styles.gridLine, { top: 5 }]} />
      <View style={[styles.gridLine, { top: 29 }]} />
      <View style={[styles.gridLine, { top: 53 }]} />
      {positions.slice(0, -1).map((position, index) => {
        const next = positions[index + 1];
        const deltaX = next.left - position.left;
        const deltaY = next.top - position.top;
        return (
          <View
            key={`line-${index}`}
            style={[
              styles.line,
              {
                backgroundColor: tone,
                left: position.left,
                top: position.top,
                transform: [{ rotate: `${Math.atan2(deltaY, deltaX)}rad` }],
                width: Math.sqrt(deltaX * deltaX + deltaY * deltaY)
              }
            ]}
          />
        );
      })}
      {positions.map((position, index) => (
        <View key={`point-${index}`} style={[styles.point, { backgroundColor: tone, left: position.left - 3.5, top: position.top - 3.5 }]} />
      ))}
      <View style={styles.axisLabels}>
        <Text style={styles.axisLabel}>{points[0]?.label}</Text>
        <Text style={styles.axisLabel}>{points[Math.floor(points.length / 2)]?.label}</Text>
        <Text style={styles.axisLabel}>{points[points.length - 1]?.label}</Text>
      </View>
      </View>
    </View>
  );
}

export function TrendCard({ series }: { series: ArchiveTrendSeries }) {
  const points = useMemo(() => chartPoints(series), [series]);
  const tone = series.metric_type === "blood_pressure" ? "#20B89D" : series.metric_type === "weight" ? "#9E78DB" : "#4F9EED";
  return (
    <View style={styles.card}>
      <View style={styles.copy}>
        <Text style={styles.label}>{series.label}趋势</Text>
        <Text style={styles.averageLabel}>平均</Text>
        <Text style={styles.value}>{averageLabel(series, points)}</Text>
        <Text style={[styles.change, { color: tone }]}>{changeLabel(series, points)}</Text>
      </View>
      <View style={styles.visual}>
        {points.length ? <MiniLineChart points={points} tone={tone} /> : <Text style={styles.empty}>暂无记录</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  averageLabel: { color: theme.colors.subtle, fontSize: 11, marginTop: 8 },
  axisLabel: { color: theme.colors.subtle, fontSize: 9 },
  axisLabels: { bottom: 0, flexDirection: "row", justifyContent: "space-between", left: 0, position: "absolute", right: 0 },
  chartRow: { flexDirection: "row", width: "100%" },
  card: { alignItems: "center", backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: 14, borderWidth: 1, flexDirection: "row", gap: 8, minHeight: 112, overflow: "hidden", padding: 12 },
  change: { fontSize: 11, fontWeight: "800", marginTop: 6 },
  chart: { height: 70, position: "relative", width: "100%" },
  copy: { flex: 0.92, minWidth: 96 },
  empty: { color: theme.colors.subtle, fontSize: 11, textAlign: "center" },
  gridLine: { backgroundColor: "#EDF3F0", height: 1, left: 0, position: "absolute", right: 0 },
  label: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" },
  line: { height: 2, position: "absolute", transformOrigin: "left center" },
  point: { borderColor: "#FFFFFF", borderRadius: 4, borderWidth: 1.5, height: 8, position: "absolute", width: 8 },
  value: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 2 },
  visual: { alignItems: "center", flex: 1, justifyContent: "center", minWidth: 0, overflow: "hidden" },
  yAxis: { height: 59, justifyContent: "space-between", paddingRight: 3, paddingTop: 1, width: 25 },
  yAxisLabel: { color: theme.colors.subtle, fontSize: 8, textAlign: "right" }
});
