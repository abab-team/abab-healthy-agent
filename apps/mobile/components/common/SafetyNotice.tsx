import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";

type SafetyNoticeProps = {
  text?: string;
};

export function SafetyNotice({
  text = "AI 基于系统记录生成内容，仅供参考，不替代医生意见与医疗建议；写入前需要你确认；提醒不是急救服务。"
}: SafetyNoticeProps) {
  return (
    <View style={styles.notice}>
      <Ionicons name="shield-checkmark-outline" size={20} color={colors.primaryDark} />
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  notice: {
    alignItems: "flex-start",
    backgroundColor: colors.blue,
    borderColor: "#b6d7ff",
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: "row",
    gap: 10,
    padding: 14
  },
  text: {
    color: "#275174",
    flex: 1,
    fontSize: 13,
    lineHeight: 20
  }
});
