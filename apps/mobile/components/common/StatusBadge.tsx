import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";

type Tone = "mint" | "blue" | "orange" | "purple" | "plain";

const toneColors: Record<Tone, string> = {
  mint: colors.mint,
  blue: colors.blue,
  orange: colors.orange,
  purple: colors.purple,
  plain: "#eef5f1"
};

export function StatusBadge({ label, tone = "mint" }: { label: string; tone?: Tone }) {
  return (
    <View style={[styles.badge, { backgroundColor: toneColors[tone] }]}>
      <Text style={styles.text}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 4
  },
  text: {
    color: colors.primaryDark,
    fontSize: 12,
    fontWeight: "700"
  }
});
