import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

export function InlineSafetyNotice() {
  return (
    <View style={styles.notice}>
      <Ionicons color={theme.colors.primaryDark} name="shield-checkmark-outline" size={14} />
      <Text style={styles.text}>以上内容基于系统内已有记录整理，不替代医生判断。</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  notice: { alignItems: "flex-start", flexDirection: "row", gap: 6, marginLeft: 4, marginTop: -4, maxWidth: "88%" },
  text: { color: theme.colors.subtle, flex: 1, fontSize: 11, lineHeight: 16 }
});
