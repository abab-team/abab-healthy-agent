import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { theme } from "@/constants/theme";

export type ArchiveTimelineItem = {
  id: string;
  date: string;
  title: string;
  detail: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone: string;
  tag?: string;
};

export function ArchiveTimelineList({ items, title = "健康时间轴" }: { items: ArchiveTimelineItem[]; title?: string }) {
  return (
    <CardBase style={styles.card}>
      <Text style={styles.heading}>{title}</Text>
      {items.map((item, index) => (
        <View key={item.id} style={styles.row}>
          <View style={styles.rail}>
            <View style={[styles.dot, { backgroundColor: item.tone }]} />
            {index < items.length - 1 ? <View style={styles.line} /> : null}
          </View>
          <View style={styles.copy}>
            <Text style={styles.date}>{item.date}</Text>
            <View style={styles.detailRow}>
              <View style={[styles.icon, { backgroundColor: `${item.tone}16` }]}>
                <Ionicons color={item.tone} name={item.icon} size={15} />
              </View>
              <View style={styles.detailCopy}>
                <Text style={styles.title}>{item.title}</Text>
                <Text numberOfLines={1} style={styles.detail}>{item.detail}</Text>
              </View>
              {item.tag ? <Text style={[styles.tag, { color: item.tone }]}>{item.tag}</Text> : null}
            </View>
          </View>
        </View>
      ))}
    </CardBase>
  );
}

const styles = StyleSheet.create({
  card: { gap: 0 },
  copy: { flex: 1, paddingBottom: 14 },
  date: { color: theme.colors.subtle, fontSize: 12, fontWeight: "700", marginBottom: 7 },
  detail: { color: theme.colors.subtle, fontSize: 12, marginTop: 3 },
  detailCopy: { flex: 1 },
  detailRow: { alignItems: "center", flexDirection: "row", gap: 9 },
  dot: { borderColor: "#FFFFFF", borderRadius: 6, borderWidth: 2, height: 12, width: 12 },
  heading: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900", marginBottom: 16 },
  icon: { alignItems: "center", borderRadius: 10, height: 31, justifyContent: "center", width: 31 },
  line: { backgroundColor: theme.colors.line, bottom: -2, position: "absolute", top: 12, width: 2 },
  rail: { alignItems: "center", alignSelf: "stretch", marginRight: 10, paddingTop: 1, width: 12 },
  row: { flexDirection: "row" },
  tag: { fontSize: 11, fontWeight: "800" },
  title: { color: theme.colors.ink, fontSize: 14, fontWeight: "800" }
});
