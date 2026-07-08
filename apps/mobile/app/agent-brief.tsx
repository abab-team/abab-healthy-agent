import { Link } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ReminderCard } from "@/components/cards/ReminderCard";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members, reminders, todos } from "@/constants/mockData";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse } from "@/types/api";

export default function AgentBriefScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [run, setRun] = useState<AgentRunResponse | null>(null);
  const [status, setStatus] = useState("尚未生成，本页不会自动发起写入动作。");
  const [loading, setLoading] = useState(false);

  async function refreshBrief() {
    setLoading(true);
    setStatus("正在生成系统内健康简报...");
    const result = await provider.runDailyHealthBrief(session.currentUserId);
    setLoading(false);
    if (result.ok && result.data) {
      setRun(result.data);
      setStatus("简报已生成。");
    } else {
      setStatus(result.error?.message ?? "生成失败，请检查 API 配置。");
    }
  }

  return (
    <AppScreen>
      <Text style={styles.title}>今日健康简报</Text>
      <SafetyNotice text="根据系统内记录生成，仅供家庭健康管理参考，不能替代医生意见或治疗建议。" />
      <StatusBadge label={loading ? "生成中" : status} tone="plain" />

      <CardBase>
        <SectionHeader title="根据系统内记录" />
        <Text style={styles.paragraph}>
          {run?.generated_content ?? "点击下方按钮后，后端模式会生成系统内健康简报；演示模式会返回本地演示简报。"}
        </Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="成员摘要" action="演示数据" />
        {members.map((member) => (
          <Text key={member.id} style={styles.line}>
            {member.name}：{member.status}
          </Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="今日待办" action="演示数据" />
        {todos.map((todo) => (
          <Text key={todo.id} style={styles.line}>{todo.title}</Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="提醒" action="演示数据" />
        {reminders.map((reminder) => (
          <ReminderCard key={reminder.id} {...reminder} />
        ))}
      </CardBase>

      <CardBase>
        <Text style={styles.paragraph}>
          如有不适或紧急情况，请联系医生或当地急救服务。本简报只整理系统内已有记录。
        </Text>
        <Pressable style={styles.button} onPress={refreshBrief}>
          <Text style={styles.buttonText}>{loading ? "生成中..." : "生成今日健康简报"}</Text>
        </Pressable>
        <Link href={routes.agentRun(run?.trace_id ?? "run-12")} style={styles.linkButton}>
          查看 Agent Run 详情
        </Link>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    marginTop: 14,
    paddingVertical: 12
  },
  buttonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "800",
    textAlign: "center"
  },
  line: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
    paddingVertical: 8
  },
  linkButton: {
    borderColor: colors.primary,
    borderRadius: 999,
    borderWidth: 1,
    color: colors.primaryDark,
    fontSize: 15,
    fontWeight: "800",
    marginTop: 10,
    overflow: "hidden",
    paddingVertical: 12,
    textAlign: "center"
  },
  paragraph: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  }
});
