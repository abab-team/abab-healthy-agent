import { Switch, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

export function QuickNoteModeToggle({ enabled, onChange }: { enabled: boolean; onChange: (value: boolean) => void }) {
  return <View style={styles.row}>
    <View style={styles.copy}><Text style={styles.title}>随手记模式</Text><Text style={styles.caption}>我会把健康情况整理成待确认草稿，不会直接写入档案。</Text></View>
    <Switch onValueChange={onChange} trackColor={{ false: theme.colors.line, true: theme.colors.primary }} value={enabled} />
  </View>;
}

const styles = StyleSheet.create({
  caption: { color: theme.colors.subtle, fontSize: 11, lineHeight: 16 },
  copy: { flex: 1, gap: 2, paddingRight: 12 },
  row: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: theme.radius.sm, flexDirection: "row", marginBottom: 8, paddingHorizontal: 12, paddingVertical: 9 },
  title: { color: theme.colors.ink, fontSize: 13, fontWeight: "800" }
});
