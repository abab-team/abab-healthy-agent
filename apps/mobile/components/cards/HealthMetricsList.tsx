import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";
import type { BloodPressureRecord, HealthMetricRecord } from "@/types/api";

type MetricId = "blood-pressure" | "sleep" | "weight" | "steps";

type MetricRow = {
  id: MetricId;
  label: string;
  detail: string;
  summary: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone: string;
  surface: string;
};

function latestMetric(metrics: HealthMetricRecord[], types: string[]) {
  return metrics.find((metric) => types.includes(metric.metric_type));
}

export function buildMetricRows(bloodPressure: BloodPressureRecord[], metrics: HealthMetricRecord[]): MetricRow[] {
  const pressure = bloodPressure[0];
  const sleep = latestMetric(metrics, ["sleep", "sleep_duration"]);
  const weight = latestMetric(metrics, ["weight"]);
  const steps = latestMetric(metrics, ["steps", "step_count"]);
  const display = (metric: HealthMetricRecord | undefined, fallback: string, suffix: string) => metric?.value_numeric !== undefined && metric?.value_numeric !== null ? `${metric.value_numeric.toLocaleString("zh-CN")}${suffix}` : fallback;
  return [
    { detail: pressure ? `最近 ${pressure.systolic}/${pressure.diastolic} mmHg` : "暂无已共享记录", icon: "pulse-outline", id: "blood-pressure", label: "血压", summary: `历史记录 ${bloodPressure.length} 条`, surface: "#FFF0EE", tone: "#F16E6B" },
    { detail: display(sleep, "暂无已共享记录", " 小时"), icon: "moon-outline", id: "sleep", label: "睡眠", summary: sleep ? "已共享最近记录" : "暂无已共享记录", surface: "#F1EFFF", tone: "#7467EC" },
    { detail: display(weight, "暂无已共享记录", " kg"), icon: "body-outline", id: "weight", label: "体重", summary: weight ? "已共享最近记录" : "暂无已共享记录", surface: "#FFF3E7", tone: "#F29445" },
    { detail: display(steps, "暂无已共享记录", " 步"), icon: "footsteps-outline", id: "steps", label: "步数", summary: steps ? "已共享最近记录" : "暂无已共享记录", surface: "#EAF9F3", tone: "#23B99B" }
  ];
}

export function HealthMetricsList({ rows, onPress }: { rows: MetricRow[]; onPress: (id: MetricId) => void }) {
  return <View style={styles.list}>{rows.map((metric) => <Pressable key={metric.id} onPress={() => onPress(metric.id)} style={styles.row}><View style={[styles.icon, { backgroundColor: metric.surface }]}><Ionicons color={metric.tone} name={metric.icon} size={23} /></View><View style={styles.copy}><Text style={styles.label}>{metric.label}</Text><Text style={styles.detail}>{metric.detail}</Text><Text style={styles.summary}>{metric.summary}</Text></View><Ionicons color={theme.colors.subtle} name="chevron-forward" size={20} /></Pressable>)}</View>;
}

const styles = StyleSheet.create({
  copy: { flex: 1 },
  detail: { color: theme.colors.ink, fontSize: 13, fontWeight: "700", marginTop: 4 },
  icon: { alignItems: "center", borderRadius: 12, height: 44, justifyContent: "center", width: 44 },
  label: { color: theme.colors.ink, fontSize: 16, fontWeight: "900" },
  list: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, overflow: "hidden" },
  row: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 12, padding: 15 },
  summary: { color: theme.colors.subtle, fontSize: 11, marginTop: 3 }
});
