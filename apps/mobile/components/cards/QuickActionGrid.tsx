import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";
import { quickActions } from "@/constants/mockData";

export function QuickActionGrid() {
  return (
    <View style={styles.grid}>
      {quickActions.map((action) => (
        <Link key={action.id} href={action.href} style={styles.item}>
          <Ionicons name={action.icon as keyof typeof Ionicons.glyphMap} size={26} color={colors.primary} />
          <Text style={styles.label}>{action.label}</Text>
        </Link>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    gap: 10
  },
  item: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    flex: 1,
    paddingHorizontal: 4,
    paddingVertical: 14,
    textAlign: "center"
  },
  label: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700",
    marginTop: 8
  }
});
