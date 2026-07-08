import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SafeResultSummary } from "@/components/common/SafeResultSummary";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { WorkflowStatusCard } from "@/components/common/WorkflowStatusCard";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { family as mockFamily, members as mockMembers } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { AgentRunResponse, FamilyMember } from "@/types/api";

const reminderTypes = ["记录提醒", "复查提醒", "资料整理提醒"];

function mockFamilyMembers(): FamilyMember[] {
  return mockMembers.map((member) => ({
    display_name: member.name,
    family_id: mockFamily.id,
    id: member.id,
    relationship_label: member.relation,
    share_status: member.shareStatus,
    user_id: member.id
  }));
}

export default function CreateAlertScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId]);
  const members = useMemo(() => overview.data?.members ?? mockFamilyMembers(), [overview.data]);
  const [selectedUserId, setSelectedUserId] = useState(session.dataMode === "api" ? session.currentUserId : "dad");
  const [title, setTitle] = useState("今晚记录血压");
  const [messageText, setMessageText] = useState("提醒家庭成员按计划记录一条健康数据。");
  const [reminderType, setReminderType] = useState(reminderTypes[0]);
  const [time, setTime] = useState("2026-07-07T20:30:00+08:00");
  const [previewRun, setPreviewRun] = useState<AgentRunResponse | null>(null);
  const [confirmedRun, setConfirmedRun] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState("等待预览。");
  const [loading, setLoading] = useState(false);
  const selectedMember = members.find((member) => member.user_id === selectedUserId || member.id === selectedUserId) ?? members[0];
  const targetUserId = selectedMember?.user_id ?? session.currentUserId;
  const familyId = selectedMember?.family_id;

  async function previewAlert() {
    setLoading(true);
    setError(null);
    setMessage("正在请求 confirmation=false 预览；预览不会写入。");
    setPreviewRun(null);
    const result = await provider.createAlertPreview({
      alertType: "medical_follow_up",
      familyId,
      level: "info",
      message: messageText,
      scheduledAt: time,
      targetUserId,
      title
    });
    setLoading(false);
    if (result.ok && result.data) {
      setPreviewRun(result.data);
      setMessage(result.data.blocked ? "后端安全阻断，未创建提醒。" : "预览已返回，尚未创建提醒。");
      return;
    }
    const errorMessage = result.error?.message ?? "预览失败，请检查权限或网络。";
    setError(errorMessage);
    setMessage(errorMessage);
  }

  async function confirmAlert() {
    if (!previewRun) {
      setMessage("请先预览提醒。");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage("正在请求 confirmation=true；成功后创建普通健康提醒。");
    const result = await provider.createAlertConfirmed({
      alertType: "medical_follow_up",
      familyId,
      level: "info",
      message: messageText,
      scheduledAt: time,
      targetUserId,
      title
    });
    setLoading(false);
    if (result.ok && result.data) {
      setConfirmedRun(result.data);
      setMessage(result.data.blocked ? "后端阻断，未创建提醒。" : "普通健康提醒已由后端创建。");
      return;
    }
    const errorMessage = result.error?.message ?? "确认失败，请检查权限或网络。";
    setError(errorMessage);
    setMessage(errorMessage);
  }

  return (
    <AppScreen>
      <Text style={styles.title}>创建健康提醒</Text>
      <SafetyNotice text="提醒不是急救；系统只创建普通健康提醒，不提供紧急服务。" />
      <View style={styles.modeRow}>
        <ApiModeBadge mode={session.dataMode} label={session.dataMode === "api" ? "后端已连接" : "演示预览"} />
        <StatusBadge label={loading ? "处理中" : message} tone="plain" />
      </View>
      {error ? <ApiErrorState message={error} /> : null}
      {overview.error ? <ApiErrorState message={overview.error} /> : null}

      <WorkflowStatusCard
        confirmText="确认后创建普通健康提醒"
        mode={session.dataMode}
        workflowType="alert_create"
      />

      <CardBase>
        <SectionHeader title="选择成员" action={overview.loading ? "加载中" : undefined} />
        <View style={styles.row}>
          {members.map((member) => (
            <Pressable key={member.id} onPress={() => setSelectedUserId(member.user_id)} style={styles.chip}>
              <StatusBadge label={member.display_name} tone={member.user_id === targetUserId ? "mint" : "plain"} />
            </Pressable>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="提醒内容" />
        <TextInput value={title} onChangeText={setTitle} style={styles.input} placeholder="提醒标题" />
        <TextInput value={messageText} onChangeText={setMessageText} style={styles.input} placeholder="提醒说明" />
        <View style={styles.row}>
          {reminderTypes.map((type) => (
            <Pressable key={type} onPress={() => setReminderType(type)} style={styles.chip}>
              <StatusBadge label={type} tone={type === reminderType ? "orange" : "plain"} />
            </Pressable>
          ))}
        </View>
        <TextInput value={time} onChangeText={setTime} style={styles.input} placeholder="提醒时间" />
        <Pressable style={styles.button} onPress={previewAlert}>
          <Text style={styles.buttonText}>预览提醒</Text>
        </Pressable>
      </CardBase>

      {previewRun ? (
        <>
          <SafeResultSummary
            note="预览结果仅用于确认前检查，不创建提醒。"
            run={previewRun}
            title={previewRun.blocked ? "安全阻断" : "预览结果"}
          />
          <CardBase>
            <SectionHeader title="确认下一步" />
            <Text style={styles.line}>确认后创建普通健康提醒；提醒不是急救，如遇紧急情况请联系医生或当地急救服务。</Text>
            <Pressable style={[styles.button, styles.confirmButton]} onPress={confirmAlert}>
              <Text style={styles.buttonText}>确认创建提醒</Text>
            </Pressable>
          </CardBase>
        </>
      ) : null}

      {confirmedRun ? (
        <SafeResultSummary
          note="确认成功后只创建普通健康提醒，不提供紧急服务。"
          run={confirmedRun}
          title={confirmedRun.blocked ? "未创建提醒" : "确认结果"}
        />
      ) : null}
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
  chip: {
    marginRight: 4
  },
  confirmButton: {
    backgroundColor: colors.primaryDark
  },
  input: {
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 12,
    padding: 12
  },
  line: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
  },
  modeRow: {
    gap: 8,
    marginTop: 8
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  }
});
