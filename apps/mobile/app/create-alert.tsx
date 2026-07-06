import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";

export default function CreateAlertScreen() {
  return (
    <AppScreen>
      <Text style={styles.title}>创建健康提醒</Text>
      <SafetyNotice text="提醒用于日常健康管理，不会代替人工处理紧急情况。" />

      <CardBase>
        <SectionHeader title="提醒信息" />
        <Text style={styles.field}>标题：爸爸今晚量血压</Text>
        <Text style={styles.field}>时间：今天 20:30</Text>
        <Text style={styles.field}>成员：爸爸</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="确认交互示意" />
        <Text style={styles.line}>Workflow：alert_create</Text>
        <Text style={styles.line}>confirmation=false：不会创建提醒，仅显示待确认状态。</Text>
        <Text style={styles.line}>confirmation=true：创建普通家庭健康提醒。</Text>
        <View style={styles.actions}>
          <StatusBadge label="确认创建" tone="mint" />
          <StatusBadge label="稍后再说" tone="orange" />
        </View>
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
  field: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "700",
    paddingVertical: 8
  },
  line: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
  },
  actions: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14
  }
});
