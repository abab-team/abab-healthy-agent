import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { BloodPressureCreateInput, HealthMetricCreateInput } from "@/types/api";

type MetricKind = "blood_pressure" | "temperature" | "weight" | "sleep_duration" | "heart_rate" | "steps";
type TimeMode = "now" | "today" | "custom";

const options: Array<{ key: MetricKind; label: string; icon: keyof typeof Ionicons.glyphMap; unit: string }> = [
  { key: "blood_pressure", label: "血压", icon: "pulse-outline", unit: "mmHg" },
  { key: "temperature", label: "体温", icon: "thermometer-outline", unit: "°C" },
  { key: "weight", label: "体重", icon: "scale-outline", unit: "kg" },
  { key: "sleep_duration", label: "睡眠", icon: "moon-outline", unit: "小时" },
  { key: "heart_rate", label: "心率", icon: "heart-outline", unit: "次/分" },
  { key: "steps", label: "步数", icon: "footsteps-outline", unit: "步" }
];

function localIso(value: Date) {
  const pad = (number: number) => String(number).padStart(2, "0");
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}:00`;
}

export default function RecordHealthMetricScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const [kind, setKind] = useState<MetricKind>("blood_pressure");
  const [timeMode, setTimeMode] = useState<TimeMode>("now");
  const [customDate, setCustomDate] = useState(localIso(new Date()));
  const [systolic, setSystolic] = useState("");
  const [diastolic, setDiastolic] = useState("");
  const [pulse, setPulse] = useState("");
  const [value, setValue] = useState("");
  const [sleepHours, setSleepHours] = useState("7");
  const [sleepMinutes, setSleepMinutes] = useState("0");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const selected = options.find((item) => item.key === kind) ?? options[0];

  function measuredAt() {
    if (timeMode === "now") return localIso(new Date());
    if (timeMode === "today") {
      const earlier = new Date();
      earlier.setHours(8, 0, 0, 0);
      return localIso(earlier);
    }
    return customDate.replace(" ", "T");
  }

  function buildPayload(): HealthMetricCreateInput | BloodPressureCreateInput | null {
    const at = measuredAt();
    if (Number.isNaN(new Date(at).getTime())) return null;
    if (kind === "blood_pressure") {
      const systolicValue = Number(systolic);
      const diastolicValue = Number(diastolic);
      if (!Number.isFinite(systolicValue) || !Number.isFinite(diastolicValue) || systolicValue <= 0 || diastolicValue <= 0) return null;
      const pulseValue = pulse.trim() ? Number(pulse) : undefined;
      return { systolic: systolicValue, diastolic: diastolicValue, ...(Number.isFinite(pulseValue) ? { pulse: pulseValue } : {}), measured_at: at };
    }
    const metricValue = kind === "sleep_duration" ? Number(sleepHours) + Number(sleepMinutes) / 60 : Number(value);
    if (!Number.isFinite(metricValue) || metricValue < 0) return null;
    return { metric_type: kind, value_numeric: metricValue, unit: kind === "sleep_duration" ? "hours" : selected.unit, measured_at: at };
  }

  async function save() {
    setError(null);
    setSuccess(false);
    const payload = buildPayload();
    if (!payload) {
      setError("请填写有效数值和记录时间。");
      return;
    }
    setSaving(true);
    const result = await provider.createHealthMetric(payload);
    setSaving(false);
    if (!result.ok) {
      setError(result.error?.message ?? "暂时无法保存，请检查后重试。");
      return;
    }
    setSuccess(true);
  }

  return (
    <AppScreen>
      <View style={styles.header}><Pressable accessibilityLabel="返回" onPress={() => router.back()}><Ionicons color={theme.colors.ink} name="chevron-back" size={26} /></Pressable><Text style={styles.title}>记录健康指标</Text><View style={styles.headerPlaceholder} /></View>
      <Text style={styles.subtitle}>选择指标后填写数值，默认按当前时间保存。</Text>
      <CardBase><Text style={styles.sectionTitle}>选择指标</Text><View style={styles.optionGrid}>{options.map((option) => <Pressable key={option.key} onPress={() => { setKind(option.key); setError(null); }} style={[styles.option, kind === option.key && styles.optionSelected]}><Ionicons color={kind === option.key ? "#FFFFFF" : theme.colors.primary} name={option.icon} size={20} /><Text style={[styles.optionText, kind === option.key && styles.optionTextSelected]}>{option.label}</Text></Pressable>)}</View></CardBase>
      <CardBase><Text style={styles.sectionTitle}>{selected.label}数值</Text>{kind === "blood_pressure" ? <View style={styles.fieldStack}><Field label="收缩压" suffix="mmHg" value={systolic} onChangeText={setSystolic} /><Field label="舒张压" suffix="mmHg" value={diastolic} onChangeText={setDiastolic} /><Field label="心率（可选）" suffix="次/分" value={pulse} onChangeText={setPulse} /></View> : kind === "sleep_duration" ? <View style={styles.sleepRow}><Field label="小时" suffix="小时" value={sleepHours} onChangeText={setSleepHours} /><Field label="分钟" suffix="分钟" value={sleepMinutes} onChangeText={setSleepMinutes} /></View> : <Field label={selected.label} suffix={selected.unit} value={value} onChangeText={setValue} />}</CardBase>
      <CardBase><Text style={styles.sectionTitle}>记录时间</Text><View style={styles.timeRow}>{([ ["now", "现在"], ["today", "今天较早时间"], ["custom", "选择日期和时间"] ] as const).map(([mode, label]) => <Pressable key={mode} onPress={() => setTimeMode(mode)} style={[styles.timeChoice, timeMode === mode && styles.timeChoiceSelected]}><Text style={[styles.timeText, timeMode === mode && styles.timeTextSelected]}>{label}</Text></Pressable>)}</View>{timeMode === "custom" ? <TextInput autoCapitalize="none" onChangeText={setCustomDate} placeholder="2026-07-16 08:30" style={styles.input} value={customDate.replace("T", " ")} /> : <Text style={styles.timeHint}>{timeMode === "now" ? "将使用当前日期和时间" : "将使用今天上午 08:00；也可选择日期和时间补录"}</Text>}</CardBase>
      <View style={styles.destination}><Ionicons color={theme.colors.primaryDark} name="folder-open-outline" size={18} /><Text style={styles.destinationText}>将保存到：档案 &gt; 健康指标 &gt; {selected.label}</Text></View>
      {error ? <ApiErrorState message={error} /> : null}
      {success ? <CardBase style={styles.success}><Text style={styles.successTitle}>已保存到健康档案</Text><Text style={styles.successText}>首页概览、趋势和健康指标历史会在刷新后显示这条记录。</Text><PrimaryButton label="查看健康指标" onPress={() => router.replace(routes.archiveMetrics)} /></CardBase> : <PrimaryButton disabled={saving || session.dataMode === "mock"} label={saving ? "正在保存..." : session.dataMode === "mock" ? "演示模式不会提交" : "保存记录"} onPress={save} />}
    </AppScreen>
  );
}

function Field({ label, suffix, value, onChangeText }: { label: string; suffix: string; value: string; onChangeText: (value: string) => void }) {
  return <View style={styles.field}><Text style={styles.fieldLabel}>{label}</Text><View style={styles.inputLine}><TextInput keyboardType="decimal-pad" onChangeText={onChangeText} placeholder="请输入" style={styles.valueInput} value={value} /><Text style={styles.suffix}>{suffix}</Text></View></View>;
}

const styles = StyleSheet.create({
  destination: { alignItems: "center", flexDirection: "row", gap: 8, paddingHorizontal: 6 },
  destinationText: { color: theme.colors.subtle, flex: 1, fontSize: 12, lineHeight: 18 },
  field: { gap: 7 }, fieldLabel: { color: theme.colors.ink, fontSize: 14, fontWeight: "800" }, fieldStack: { gap: 14 },
  header: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" }, headerPlaceholder: { width: 26 }, title: { color: theme.colors.ink, fontSize: 20, fontWeight: "900" }, subtitle: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19, marginTop: -8 },
  input: { borderColor: theme.colors.line, borderRadius: 12, borderWidth: 1, color: theme.colors.ink, marginTop: 12, padding: 12 }, inputLine: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row" }, option: { alignItems: "center", borderColor: theme.colors.line, borderRadius: 12, borderWidth: 1, flexDirection: "row", gap: 7, paddingHorizontal: 11, paddingVertical: 10 }, optionGrid: { flexDirection: "row", flexWrap: "wrap", gap: 9, marginTop: 12 }, optionSelected: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary }, optionText: { color: theme.colors.ink, fontSize: 13, fontWeight: "800" }, optionTextSelected: { color: "#FFFFFF" },
  sectionTitle: { color: theme.colors.ink, fontSize: 16, fontWeight: "900" }, sleepRow: { flexDirection: "row", gap: 12 }, success: { backgroundColor: theme.colors.tealSoft, gap: 8 }, successText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19 }, successTitle: { color: theme.colors.primaryDark, fontSize: 16, fontWeight: "900" }, suffix: { color: theme.colors.subtle, fontSize: 13, paddingBottom: 10 }, timeChoice: { alignItems: "center", borderRadius: 16, flex: 1, paddingHorizontal: 4, paddingVertical: 10 }, timeChoiceSelected: { backgroundColor: theme.colors.primary }, timeHint: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 10 }, timeRow: { backgroundColor: "#EEF4F1", borderRadius: 18, flexDirection: "row", marginTop: 12, padding: 3 }, timeText: { color: theme.colors.subtle, fontSize: 11, fontWeight: "800", textAlign: "center" }, timeTextSelected: { color: "#FFFFFF" }, valueInput: { color: theme.colors.ink, flex: 1, fontSize: 18, fontWeight: "800", paddingVertical: 9 }
});
