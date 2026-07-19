import { Ionicons } from "@expo/vector-icons";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { ArchiveTimelineItem, ArchiveTimelineList } from "@/components/cards/ArchiveTimelineList";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";

const categories = ["全部", "指标", "症状", "文档", "就医"] as const;

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "时间待补充";
  return date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" });
}

function metricDetail(type: string, value: number | null | undefined, unit: string | null | undefined) {
  if (value === null || value === undefined) return "已记录";
  if (type === "sleep_duration") {
    const hours = Math.floor(value);
    const minutes = Math.round((value - hours) * 60);
    return `${hours} 小时${minutes ? ` ${minutes} 分钟` : ""}`;
  }
  const label = type === "heart_rate" ? "次/分" : type === "steps" ? "步" : unit ?? "";
  return `${value.toLocaleString("zh-CN")}${label ? ` ${label}` : ""}`;
}

function metricTitle(type: string) {
  return ({ heart_rate: "心率", sleep_duration: "睡眠", steps: "步数", temperature: "体温", weight: "体重" } as Record<string, string>)[type] ?? "健康指标";
}

export default function ArchiveRecordsScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const resource = useApiResource(() => provider.getPersonalArchiveRecentRecords(), [session.currentUserId, session.dataMode]);
  const [category, setCategory] = useState<(typeof categories)[number]>("全部");
  const [query, setQuery] = useState("");
  const records = useMemo<ArchiveTimelineItem[]>(() => {
    const data = resource.data;
    if (!data) return [];
    return [
      ...data.bloodPressure.map((item) => ({ date: item.recorded_at, detail: `${item.systolic}/${item.diastolic} mmHg`, icon: "pulse-outline" as const, id: item.id, tag: "指标", title: "血压记录", tone: theme.colors.primary })),
      ...data.metrics.map((item) => ({ date: item.measured_at, detail: metricDetail(item.metric_type, item.value_numeric, item.unit), icon: "pulse-outline" as const, id: item.id, tag: "指标", title: `${metricTitle(item.metric_type)}记录`, tone: theme.colors.primary })),
      ...data.symptoms.map((item) => ({ date: item.recorded_at, detail: item.summary, icon: "heart-outline" as const, id: item.id, tag: "症状", title: item.title || "症状记录", tone: "#F38A69" })),
      ...data.documents.map((item) => ({ date: item.document_date ?? item.confirmed_at ?? item.created_at ?? "", detail: item.file_name, icon: "document-text-outline" as const, id: item.id, tag: "文档", title: item.title || "健康资料", tone: "#5E9CE6" })),
      ...data.medicalEvents.map((item) => ({ date: item.event_date ?? item.created_at ?? "", detail: item.summary ?? item.hospital_or_org ?? "已保存的健康事件", icon: "medical-outline" as const, id: item.id, tag: "就医", title: item.title ?? item.event_type ?? "健康事件", tone: "#E89545" }))
    ].filter((item) => item.date).sort((left, right) => new Date(right.date).getTime() - new Date(left.date).getTime()).map((item) => ({ ...item, date: formatDate(item.date) }));
  }, [resource.data]);
  const items = useMemo(() => records.filter((record) => {
    const categoryMatched = category === "全部" || record.tag === category;
    return categoryMatched && `${record.title}${record.detail}`.toLowerCase().includes(query.trim().toLowerCase());
  }), [category, query, records]);

  return (
    <AppScreen>
      <ArchiveSubHeader title="全部记录" trailing="filter" />
      <View style={styles.search}><Ionicons color={theme.colors.subtle} name="search-outline" size={18} /><TextInput onChangeText={setQuery} placeholder="搜索记录、指标、症状、文档…" placeholderTextColor={theme.colors.subtle} style={styles.input} value={query} /></View>
      <View style={styles.categories}>{categories.map((item) => <Pressable key={item} onPress={() => setCategory(item)} style={[styles.category, category === item ? styles.categoryActive : null]}><Text style={[styles.categoryText, category === item ? styles.categoryTextActive : null]}>{item}</Text></Pressable>)}</View>
      {resource.error ? <ApiErrorState message={resource.error} /> : null}
      {items.length ? <ArchiveTimelineList items={items} title="按时间查看" /> : <Text style={styles.empty}>{resource.loading ? "正在读取记录…" : "系统内暂无符合条件的记录。"}</Text>}
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  categories: { flexDirection: "row", gap: 8 },
  category: { backgroundColor: "#EEF3F1", borderRadius: theme.radius.pill, paddingHorizontal: 15, paddingVertical: 8 },
  categoryActive: { backgroundColor: theme.colors.primary },
  categoryText: { color: theme.colors.subtle, fontSize: 12, fontWeight: "800" },
  categoryTextActive: { color: "#FFFFFF" },
  empty: { color: theme.colors.subtle, fontSize: 14, padding: theme.spacing.lg, textAlign: "center" },
  input: { color: theme.colors.ink, flex: 1, fontSize: 14, height: 42 },
  search: { alignItems: "center", backgroundColor: "#EFF4F2", borderRadius: theme.radius.pill, flexDirection: "row", gap: 8, paddingHorizontal: 14 }
});
