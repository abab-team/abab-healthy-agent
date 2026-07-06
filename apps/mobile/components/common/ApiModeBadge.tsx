import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";
import type { DataMode } from "@/types/api";

export function ApiModeBadge({ mode, label }: { mode: DataMode; label?: string }) {
  return (
    <View style={[styles.badge, mode === "api" ? styles.api : styles.mock]}>
      <Text style={styles.text}>{label ?? (mode === "api" ? "API" : "Mock")}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  api: {
    backgroundColor: colors.blue
  },
  badge: {
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 4
  },
  mock: {
    backgroundColor: colors.orange
  },
  text: {
    color: colors.primaryDark,
    fontSize: 12,
    fontWeight: "800"
  }
});
