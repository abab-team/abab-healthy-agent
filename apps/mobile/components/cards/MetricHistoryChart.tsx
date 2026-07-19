import { useMemo, useState } from "react";
import { LayoutChangeEvent, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";
import type { ArchiveTrendSeries } from "@/types/api";

type LinePoint = { label: string; value: number };
type AxisRange = { min: number; max: number; ticks: number[] };

function buildPoints(series: ArchiveTrendSeries, field: "value" | "systolic" | "diastolic"): LinePoint[] {
  return series.points.slice(-8).map((point) => ({
    label: point.measured_at.slice(5, 10).replace("-", "/"),
    value: field === "value" ? point.value ?? point.systolic ?? 0 : point[field] ?? 0
  })).filter((point) => Number.isFinite(point.value));
}

function niceStep(value: number) {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  const multiplier = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return multiplier * magnitude;
}

function axisRange(values: number[]): AxisRange {
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const span = Math.max(rawMax - rawMin, Math.abs(rawMax) * 0.08, 1);
  const step = niceStep(span / 3);
  const min = Math.floor((rawMin - step * 0.5) / step) * step;
  const max = Math.ceil((rawMax + step * 0.5) / step) * step;
  const count = Math.max(Math.round((max - min) / step), 1);
  return { max, min, ticks: Array.from({ length: count + 1 }, (_, index) => max - index * step) };
}

function formatTick(value: number) {
  return Math.abs(value) < 10 && !Number.isInteger(value) ? value.toFixed(1) : String(Math.round(value));
}

function ChartLine({ color, points, range, width }: { color: string; points: LinePoint[]; range: AxisRange; width: number }) {
  const plotHeight = 126;
  const positions = points.map((point, index) => ({
    left: points.length === 1 ? width / 2 : 5 + (index / (points.length - 1)) * Math.max(width - 10, 0),
    top: 5 + ((range.max - point.value) / Math.max(range.max - range.min, 1)) * (plotHeight - 10)
  }));
  return <>{positions.slice(0, -1).map((position, index) => {
    const next = positions[index + 1];
    const deltaX = next.left - position.left;
    const deltaY = next.top - position.top;
    return <View key={`line-${index}`} style={[styles.line, { backgroundColor: color, left: position.left, top: position.top, transform: [{ rotate: `${Math.atan2(deltaY, deltaX)}rad` }], width: Math.sqrt(deltaX * deltaX + deltaY * deltaY) }]} />;
  })}{positions.map((position, index) => <View key={`dot-${index}`} style={[styles.dot, { backgroundColor: color, left: position.left - 3, top: position.top - 3 }]} />)}</>;
}

export function MetricHistoryChart({ series }: { series: ArchiveTrendSeries }) {
  const [width, setWidth] = useState(0);
  const isPressure = series.metric_type === "blood_pressure";
  const primary = useMemo(() => buildPoints(series, isPressure ? "systolic" : "value"), [isPressure, series]);
  const secondary = useMemo(() => isPressure ? buildPoints(series, "diastolic") : [], [isPressure, series]);
  const range = useMemo(() => {
    const values = [...primary, ...secondary].map((point) => point.value);
    return values.length ? axisRange(values) : { max: 1, min: 0, ticks: [1, 0] };
  }, [primary, secondary]);
  const labels = primary.length ? [primary[0].label, primary[Math.floor(primary.length / 2)].label, primary[primary.length - 1].label] : [];
  if (!primary.length) return <View style={styles.emptyWrap}><Text style={styles.empty}>系统内暂无趋势记录</Text></View>;
  return (
    <View style={styles.chartRow}>
      <View style={styles.yAxis}>{range.ticks.map((tick) => <Text key={tick} style={styles.yLabel}>{formatTick(tick)}</Text>)}</View>
      <View onLayout={(event: LayoutChangeEvent) => setWidth(event.nativeEvent.layout.width)} style={styles.plot}>
        {range.ticks.map((tick, index) => <View key={tick} style={[styles.grid, { top: 5 + (index / Math.max(range.ticks.length - 1, 1)) * 116 }]} />)}
        <ChartLine color="#1DB69A" points={primary} range={range} width={width} />
        {secondary.length ? <ChartLine color="#5A92E6" points={secondary} range={range} width={width} /> : null}
        <View style={styles.axis}>{labels.map((label, index) => <Text key={`${label}-${index}`} style={styles.axisText}>{label}</Text>)}</View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  axis: { bottom: 0, flexDirection: "row", justifyContent: "space-between", left: 0, position: "absolute", right: 0 },
  axisText: { color: theme.colors.subtle, fontSize: 10 },
  chartRow: { flexDirection: "row", height: 152 },
  dot: { borderColor: "#FFFFFF", borderRadius: 4, borderWidth: 1.5, height: 8, position: "absolute", width: 8 },
  empty: { color: theme.colors.subtle, fontSize: 13 },
  emptyWrap: { alignItems: "center", height: 152, justifyContent: "center" },
  grid: { backgroundColor: theme.colors.line, height: 1, left: 0, position: "absolute", right: 0 },
  line: { height: 2, position: "absolute", transformOrigin: "left center" },
  plot: { flex: 1, height: 152, position: "relative" },
  yAxis: { height: 126, justifyContent: "space-between", paddingBottom: 1, paddingRight: 7, paddingTop: 1, width: 36 },
  yLabel: { color: theme.colors.subtle, fontSize: 10, textAlign: "right" }
});
