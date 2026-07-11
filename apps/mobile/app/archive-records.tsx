import { Ionicons } from "@expo/vector-icons";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { ArchiveTimelineItem, ArchiveTimelineList } from "@/components/cards/ArchiveTimelineList";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";

const categories = ["全部", "指标", "症状", "文档", "就医"] as const;

const records: ArchiveTimelineItem[] = [
  { id: "pressure", date: "今天 07:30", detail: "120/78 mmHg", icon: "pulse-outline", tag: "指标", title: "血压记录", tone: theme.colors.primary },
  { id: "sleep", date: "昨天 22:10", detail: "7.2 小时", icon: "moon-outline", tag: "指标", title: "睡眠记录", tone: "#5B89E8" },
  { id: "weight", date: "昨天 07:15", detail: "62.1 kg", icon: "body-outline", tag: "指标", title: "体重记录", tone: "#8C6BD9" },
  { id: "symptom", date: "7 月 9 日 10:30", detail: "已保存为待确认草稿", icon: "heart-outline", tag: "草稿", title: "症状记录", tone: "#F38A69" },
  { id: "document", date: "7 月 8 日 16:20", detail: "2026 年度体检报告.pdf", icon: "document-text-outline", tag: "文档", title: "上传健康资料", tone: "#5E9CE6" },
  { id: "visit", date: "6 月 28 日 09:00", detail: "系统内已整理的就医记录", icon: "medical-outline", tag: "就医", title: "内科复查", tone: "#E89545" }
];

export default function ArchiveRecordsScreen() {
  const [category, setCategory] = useState<(typeof categories)[number]>("全部");
  const [query, setQuery] = useState("");
  const items = useMemo(() => records.filter((record) => {
    const categoryMatched = category === "全部" || record.tag === category || (category === "指标" && record.tag === "指标");
    return categoryMatched && `${record.title}${record.detail}`.toLowerCase().includes(query.trim().toLowerCase());
  }), [category, query]);

  return (
    <AppScreen>
      <ArchiveSubHeader title="全部记录" trailing="filter" />
      <View style={styles.search}><Ionicons color={theme.colors.subtle} name="search-outline" size={18} /><TextInput onChangeText={setQuery} placeholder="搜索记录、指标、症状、文档…" placeholderTextColor={theme.colors.subtle} style={styles.input} value={query} /></View>
      <View style={styles.categories}>
        {categories.map((item) => <Pressable key={item} onPress={() => setCategory(item)} style={[styles.category, category === item ? styles.categoryActive : null]}><Text style={[styles.categoryText, category === item ? styles.categoryTextActive : null]}>{item}</Text></Pressable>)}
      </View>
      <Text style={styles.month}>2026 年 7 月</Text>
      {items.length ? <ArchiveTimelineList items={items} title="按时间查看" /> : <Text style={styles.empty}>系统内暂无符合条件的记录。</Text>}
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
  month: { color: theme.colors.ink, fontSize: 16, fontWeight: "900", marginTop: 2 },
  search: { alignItems: "center", backgroundColor: "#EFF4F2", borderRadius: theme.radius.pill, flexDirection: "row", gap: 8, paddingHorizontal: 14 }
});
