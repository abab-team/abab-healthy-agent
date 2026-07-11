import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Switch, Text, View } from "react-native";
import { theme } from "@/constants/theme";

type SettingsToggleRowProps = {
  title: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
  value: boolean;
  onValueChange: (value: boolean) => void;
  last?: boolean;
};

export function SettingsToggleRow({ title, description, icon, value, onValueChange, last = false }: SettingsToggleRowProps) {
  return (
    <View style={[styles.row, last ? styles.last : null]}>
      <View style={styles.iconWrap}><Ionicons color={theme.colors.primary} name={icon} size={20} /></View>
      <View style={styles.copy}><Text style={styles.title}>{title}</Text><Text style={styles.description}>{description}</Text></View>
      <Switch onValueChange={onValueChange} thumbColor="#FFFFFF" trackColor={{ false: "#D8E1DE", true: theme.colors.primary }} value={value} />
    </View>
  );
}

const styles = StyleSheet.create({
  copy: { flex: 1 },
  description: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 3 },
  iconWrap: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 12, height: 40, justifyContent: "center", width: 40 },
  last: { borderBottomWidth: 0 },
  row: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 11, paddingVertical: 13 },
  title: { color: theme.colors.ink, fontSize: 15, fontWeight: "800" }
});
