import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";

export function ApiErrorState({ message }: { message: string }) {
  return (
    <View style={styles.box}>
      <Text style={styles.title}>后端暂不可用</Text>
      <Text style={styles.message}>{message}</Text>
      <Text style={styles.hint}>请检查 Data Mode、API Base URL、X-Current-User-Id 与后端服务状态。</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    backgroundColor: colors.orange,
    borderRadius: 14,
    marginTop: 10,
    padding: 12
  },
  hint: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 6
  },
  message: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 19,
    marginTop: 4
  },
  title: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "900"
  }
});
