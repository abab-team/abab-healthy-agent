import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { theme } from "@/constants/theme";

type ArchiveRecentItem = {
  id: string;
  title: string;
  detail: string;
  date: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone: string;
};

export function ArchiveRecentList({ items, onViewAll, title = "最近归档" }: { items: ArchiveRecentItem[]; onViewAll: () => void; title?: string }) {
  return (
    <CardBase>
      <View style={styles.heading}>
        <Text style={styles.title}>{title}</Text>
        <Pressable onPress={onViewAll}><Text style={styles.action}>查看全部</Text></Pressable>
      </View>
      {items.map((item) => (
        <View key={item.id} style={styles.row}>
          <View style={[styles.dot, { backgroundColor: item.tone }]} />
          <Ionicons color={theme.colors.primaryDark} name={item.icon} size={17} />
          <Text style={styles.itemTitle}>{item.title}</Text>
          <Text numberOfLines={1} style={styles.detail}>{item.detail}</Text>
          <Text style={styles.date}>{item.date}</Text>
        </View>
      ))}
      {!items.length ? <Text style={styles.empty}>系统内暂无最近归档。</Text> : null}
    </CardBase>
  );
}

const styles = StyleSheet.create({
  action: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  date: { color: theme.colors.subtle, fontSize: 10 },
  detail: { color: theme.colors.ink, flex: 1, fontSize: 12, fontWeight: "700" },
  empty: { color: theme.colors.subtle, fontSize: 13, paddingVertical: 12 },
  dot: { borderRadius: 4, height: 7, width: 7 },
  heading: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", marginBottom: 7 },
  itemTitle: { color: theme.colors.subtle, fontSize: 12 },
  row: { alignItems: "center", borderTopColor: theme.colors.line, borderTopWidth: 1, flexDirection: "row", gap: 7, minHeight: 42 },
  title: { color: theme.colors.ink, fontSize: 16, fontWeight: "900" }
});
