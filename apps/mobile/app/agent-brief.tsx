import { StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ReminderCard } from "@/components/cards/ReminderCard";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members, reminders, todos } from "@/constants/mockData";

export default function AgentBriefScreen() {
  return (
    <AppScreen>
      <Text style={styles.title}>今日健康简报</Text>
      <SafetyNotice text="根据系统内记录生成，仅供家庭健康管理参考，不能替代医生诊断或治疗建议。" />

      <CardBase>
        <SectionHeader title="根据系统内记录" />
        <Text style={styles.paragraph}>已为你整理最近 7 天的家庭健康记录摘要。</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="成员摘要" />
        {members.map((member) => (
          <Text key={member.id} style={styles.line}>
            {member.name}：{member.status}
          </Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="今日待办" />
        {todos.map((todo) => (
          <Text key={todo.id} style={styles.line}>{todo.title}</Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="提醒" />
        {reminders.map((reminder) => (
          <ReminderCard key={reminder.id} {...reminder} />
        ))}
      </CardBase>

      <CardBase>
        <Text style={styles.paragraph}>
          如有不适或紧急情况，请联系医生或当地急救服务。本简报只整理系统内已有记录。
        </Text>
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
  paragraph: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10
  },
  line: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
    paddingVertical: 8
  }
});
