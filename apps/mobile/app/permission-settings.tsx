import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";

const permissionRows = [
  "健康档案查看",
  "血压记录查看",
  "症状记录查看",
  "健康事件查看",
  "提醒查看",
  "提醒创建"
];

export default function PermissionSettingsScreen() {
  return (
    <AppScreen>
      <Text style={styles.title}>共享权限设置</Text>
      <SafetyNotice text="这里展示家庭共享权限的演示状态，真实权限仍以后端检查为准。" />
      <CardBase>
        <SectionHeader title="权限概览" />
        {permissionRows.map((row) => (
          <View key={row} style={styles.row}>
            <Text style={styles.rowText}>{row}</Text>
            <StatusBadge label="已开启" tone="mint" />
          </View>
        ))}
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  },
  row: {
    alignItems: "center",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 12
  },
  rowText: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "700"
  }
});
