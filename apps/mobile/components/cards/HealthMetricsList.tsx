import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";
import type { BloodPressureRecord, HealthMetricRecord } from "@/types/api";

type MetricId = "blood-pressure" | "sleep" | "weight" | "steps" | "heart-rate" | "temperature";
type MetricRow = { id: MetricId; label: string; detail: string; summary: string; icon: keyof typeof Ionicons.glyphMap; tone: string; surface: string };

function latestMetric(metrics: HealthMetricRecord[], types: string[]) { return metrics.find((metric) => types.includes(metric.metric_type)); }
function display(metric: HealthMetricRecord | undefined, suffix: string) { return metric?.value_numeric !== undefined && metric?.value_numeric !== null ? `${metric.value_numeric.toLocaleString("zh-CN")}${suffix}` : "暂无已记录"; }

export function buildMetricRows(bloodPressure: BloodPressureRecord[], metrics: HealthMetricRecord[]): MetricRow[] {
  const pressure = bloodPressure[0]; const sleep = latestMetric(metrics, ["sleep", "sleep_duration"]); const weight = latestMetric(metrics, ["weight"]); const steps = latestMetric(metrics, ["steps", "step_count"]); const heartRate = latestMetric(metrics, ["heart_rate"]); const temperature = latestMetric(metrics, ["temperature"]);
  return [
    { id: "blood-pressure", label: "血压", detail: pressure ? `最近 ${pressure.systolic}/${pressure.diastolic} mmHg` : "暂无已记录", summary: `历史记录 ${bloodPressure.length} 条`, icon: "pulse-outline", surface: "#FFF0EE", tone: "#F16E6B" },
    { id: "sleep", label: "睡眠", detail: display(sleep, " 小时"), summary: sleep ? "已有最近记录" : "暂无已记录", icon: "moon-outline", surface: "#F1EFFF", tone: "#7467EC" },
    { id: "weight", label: "体重", detail: display(weight, " kg"), summary: weight ? "已有最近记录" : "暂无已记录", icon: "body-outline", surface: "#FFF3E7", tone: "#F29445" },
    { id: "steps", label: "步数", detail: display(steps, " 步"), summary: steps ? "已有最近记录" : "暂无已记录", icon: "footsteps-outline", surface: "#EAF9F3", tone: "#23B99B" },
    { id: "heart-rate", label: "心率", detail: display(heartRate, " 次/分"), summary: heartRate ? "已有最近记录" : "暂无已记录", icon: "heart-outline", surface: "#FFF0EE", tone: "#F16E6B" },
    { id: "temperature", label: "体温", detail: display(temperature, " °C"), summary: temperature ? "已有最近记录" : "暂无已记录", icon: "thermometer-outline", surface: "#EEF7FF", tone: "#3297E8" }
  ];
}

export function HealthMetricsList({ rows, onPress }: { rows: MetricRow[]; onPress: (id: MetricId) => void }) {
  return <View style={styles.list}>{rows.map((metric) => <Pressable key={metric.id} onPress={() => onPress(metric.id)} style={styles.row}><View style={[styles.icon, { backgroundColor: metric.surface }]}><Ionicons color={metric.tone} name={metric.icon} size={23} /></View><View style={styles.copy}><Text style={styles.label}>{metric.label}</Text><Text style={styles.detail}>{metric.detail}</Text><Text style={styles.summary}>{metric.summary}</Text></View><Ionicons color={theme.colors.subtle} name="chevron-forward" size={20} /></Pressable>)}</View>;
}

const styles = StyleSheet.create({ copy: { flex: 1 }, detail: { color: theme.colors.ink, fontSize: 13, fontWeight: "700", marginTop: 4 }, icon: { alignItems: "center", borderRadius: 12, height: 44, justifyContent: "center", width: 44 }, label: { color: theme.colors.ink, fontSize: 16, fontWeight: "900" }, list: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, overflow: "hidden" }, row: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 12, padding: 15 }, summary: { color: theme.colors.subtle, fontSize: 11, marginTop: 3 } });
