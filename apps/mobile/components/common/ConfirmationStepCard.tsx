import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";

export function ConfirmationStepCard({ confirmText }: { confirmText: string }) {
  return (
    <View style={styles.steps}>
      <View style={styles.step}>
        <Text style={styles.stepTitle}>1. 预览</Text>
        <Text style={styles.stepText}>confirmation=false</Text>
        <Text style={styles.stepText}>预览不会写入</Text>
      </View>
      <View style={styles.step}>
        <Text style={styles.stepTitle}>2. 确认</Text>
        <Text style={styles.stepText}>confirmation=true</Text>
        <Text style={styles.stepText}>{confirmText}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  step: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    flex: 1,
    padding: 12
  },
  stepText: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4
  },
  stepTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "900"
  },
  steps: {
    flexDirection: "row",
    gap: 10,
    marginTop: 12
  }
});
