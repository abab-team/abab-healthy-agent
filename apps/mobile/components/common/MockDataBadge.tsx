import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";

export function MockDataBadge({ label = "演示数据" }: { label?: string }) {
  return (
    <View style={styles.badge}>
      <Text style={styles.text}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    backgroundColor: colors.orange,
    borderRadius: 999,
    marginTop: 8,
    paddingHorizontal: 9,
    paddingVertical: 4
  },
  text: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: "800"
  }
});
