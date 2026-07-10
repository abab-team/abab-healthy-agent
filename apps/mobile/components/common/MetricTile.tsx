import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

type MetricTileProps = {
  label: string;
  value: string;
  note: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone?: "teal" | "blue" | "coral" | "lavender";
  wide?: boolean;
};

const backgrounds = {
  teal: theme.colors.tealSoft,
  blue: theme.colors.blueSoft,
  coral: theme.colors.coralSoft,
  lavender: theme.colors.lavenderSoft
};

export function MetricTile({ label, value, note, icon, tone = "teal", wide = false }: MetricTileProps) {
  return (
    <View style={[styles.tile, wide ? styles.wide : null, { backgroundColor: backgrounds[tone] }]}>
      <Ionicons color={theme.colors.primaryDark} name={icon} size={21} />
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.note}>{note}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  label: { color: theme.colors.subtle, fontSize: 12, marginTop: 9 },
  note: { color: theme.colors.subtle, fontSize: 11, lineHeight: 16, marginTop: 4 },
  tile: { borderRadius: theme.radius.md, minHeight: 132, padding: 13, width: "48%" },
  value: { color: theme.colors.ink, fontSize: 19, fontWeight: "900", marginTop: 4 },
  wide: { minHeight: 92, width: "100%" }
});
