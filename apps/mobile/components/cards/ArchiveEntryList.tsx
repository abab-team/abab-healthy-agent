import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

export type ArchiveEntry = {
  id: string;
  title: string;
  description: string;
  count: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone: "teal" | "blue" | "orange" | "purple" | "mint";
  onPress: () => void;
};

const tones = {
  teal: theme.colors.tealSoft,
  blue: theme.colors.blueSoft,
  orange: theme.colors.coralSoft,
  purple: theme.colors.lavenderSoft,
  mint: "#ECFAF4"
};

export function ArchiveEntryList({ entries }: { entries: ArchiveEntry[] }) {
  return (
    <View style={styles.list}>
      {entries.map((entry) => (
        <Pressable key={entry.id} onPress={entry.onPress} style={styles.row}>
          <View style={[styles.iconWrap, { backgroundColor: tones[entry.tone] }]}>
            <Ionicons color={theme.colors.primaryDark} name={entry.icon} size={22} />
          </View>
          <View style={styles.copy}>
            <Text style={styles.title}>{entry.title}</Text>
            <Text style={styles.description}>{entry.description}</Text>
          </View>
          <View style={styles.trailing}>
            <Text style={styles.count}>{entry.count}</Text>
            <Ionicons color={theme.colors.subtle} name="chevron-forward" size={17} />
          </View>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  copy: { flex: 1 },
  count: { color: theme.colors.subtle, fontSize: 11, fontWeight: "800" },
  description: { color: theme.colors.subtle, fontSize: 11, lineHeight: 17, marginTop: 3 },
  iconWrap: { alignItems: "center", borderRadius: 15, height: 42, justifyContent: "center", width: 42 },
  list: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, paddingHorizontal: 14 },
  row: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 12, minHeight: 68, paddingVertical: 10 },
  title: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" },
  trailing: { alignItems: "center", flexDirection: "row", gap: 5 }
});
