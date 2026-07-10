import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

export type Period = "7天" | "30天" | "90天" | "全部";

export function PeriodSelector({ value, onChange }: { value: Period; onChange: (period: Period) => void }) {
  const periods: Period[] = ["7天", "30天", "90天", "全部"];
  return (
    <View style={styles.container}>
      {periods.map((period) => (
        <Pressable key={period} onPress={() => onChange(period)} style={[styles.item, value === period ? styles.selected : null]}>
          <Text style={[styles.label, value === period ? styles.selectedLabel : null]}>{period}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: "#F0F5F2", borderRadius: theme.radius.pill, flexDirection: "row", padding: 3 },
  item: { alignItems: "center", borderRadius: theme.radius.pill, flex: 1, paddingVertical: 8 },
  label: { color: theme.colors.subtle, fontSize: 12, fontWeight: "800" },
  selected: { backgroundColor: theme.colors.primary },
  selectedLabel: { color: "#FFFFFF" }
});
