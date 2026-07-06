import { Link } from "expo-router";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { family as mockFamily, members as mockMembers } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { AgentRunResponse, FamilyMember } from "@/types/api";

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

function summaryText(run: AgentRunResponse | null): string {
  return run?.generated_content ?? run?.message ?? "系统内暂无可展示摘要。";
}

export default function CreateHealthEventDraftScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId]);
  const members = useMemo(() => overview.data?.members ?? mockFamilyMembers(), [overview.data]);
  const [selectedUserId, setSelectedUserId] = useState(session.dataMode === "api" ? session.currentUserId : "mom");
  const [title, setTitle] = useState("复查记录整理");
  const [summary, setSummary] = useState("5 月20日复查后，准备整理成待确认健康事件草稿。");
  const [eventDate, setEventDate] = useState("2026-07-06");
  const [previewRun, setPreviewRun] = useState<AgentRunResponse | null>(null);
  const [confirmedRun, setConfirmedRun] = useState<AgentRunResponse | null>(null);
  const [message, setMessage] = useState("等待输入。");
  const [loading, setLoading] = useState(false);
  const selectedMember = members.find((member) => member.user_id === selectedUserId || member.id === selectedUserId) ?? members[0];
  const targetUserId = selectedMember?.user_id ?? session.currentUserId;
  const familyId = selectedMember?.family_id;

  async function generatePreview() {
    setLoading(true);
    setMessage("正在请求 confirmation=false 预览；预览不会写入。");
    setPreviewRun(null);
    const result = await provider.createMedicalEventDraftPreview({
      eventDate,
      eventType: "follow_up",
      familyId,
      summary,
      targetUserId,
      title
    });
    setLoading(false);
    if (result.ok && result.data) {
      setPreviewRun(result.data);
      setMessage(result.data.blocked ? "后端安全阻断，未写入草稿。" : "预览已返回，尚未写入。");
      return;
    }
    setMessage(result.error?.message ?? "预览失败，请检查权限或网络。");
  }

  async function confirmDraft() {
    if (!previewRun) {
      setMessage("请先生成预览。");
      return;
    }
    setLoading(true);
    setMessage("正在请求 confirmation=true；成功后创建待确认健康事件草稿。");
    const result = await provider.createMedicalEventDraftConfirmed({
      eventDate,
      eventType: "follow_up",
      familyId,
      summary,
      targetUserId,
      title
    });
    setLoading(false);
    if (result.ok && result.data) {
      setConfirmedRun(result.data);
      setMessage(result.data.blocked ? "后端阻断，未创建草稿。" : "待确认健康事件草稿已由后端创建。");
      return;
    }
    setMessage(result.error?.message ?? "确认失败，请检查权限或网络。");
  }

  return (
    <AppScreen>
      <Text style={styles.title}>创建健康事件草稿</Text>
      <SafetyNotice text="此页面只创建待确认草稿，不创建正式健康事件；内容不替代医生建议。" />
      <View style={styles.modeRow}>
        <ApiModeBadge mode={session.dataMode} label={session.dataMode === "api" ? "API Agent workflow" : "Mock 静态预览"} />
        <StatusBadge label={loading ? "处理中" : message} tone="plain" />
      </View>
      {overview.error ? <ApiErrorState message={overview.error} /> : null}

      <CardBase>
        <SectionHeader title="当前写入状态" />
        <Text style={styles.line}>
          {session.dataMode === "api"
            ? "api mode 将通过 POST /api/v1/agent/runs 调用 medical_event_draft_create。"
            : "mock mode 只演示交互，不会真实提交。"}
        </Text>
        <Text style={styles.line}>预览使用 confirmation=false；确认使用 confirmation=true。</Text>
      </CardBase>

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
        <SectionHeader title="草稿内容" />
        <TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="标题" />
        <TextInput style={styles.input} value={eventDate} onChangeText={setEventDate} placeholder="日期，例如 2026-07-06" />
        <TextInput
          multiline
          style={[styles.input, styles.multiline]}
          value={summary}
          onChangeText={setSummary}
          placeholder="输入要整理的健康事项"
        />
        <Pressable style={styles.button} onPress={generatePreview}>
          <Text style={styles.buttonText}>生成草稿预览</Text>
        </Pressable>
      </CardBase>

      {previewRun ? (
        <CardBase>
          <SectionHeader title="预览结果" />
          <Text style={styles.line}>Workflow：{previewRun.workflow_type}</Text>
          <Text style={styles.line}>Status：{previewRun.status}</Text>
          <Text style={styles.generated}>{summaryText(previewRun)}</Text>
          <Text style={styles.line}>预览不会写入；确认后才创建待确认草稿。</Text>
          <View style={styles.actions}>
            <Pressable style={[styles.button, styles.confirmButton]} onPress={confirmDraft}>
              <Text style={styles.buttonText}>确认创建草稿</Text>
            </Pressable>
            <Link href={routes.agentRun(previewRun.trace_id)} style={styles.linkButton}>
              查看 Run 详情
            </Link>
          </View>
        </CardBase>
      ) : null}

      {confirmedRun ? (
        <CardBase>
          <SectionHeader title="确认结果" />
          <Text style={styles.line}>Trace：{confirmedRun.trace_id}</Text>
          <Text style={styles.generated}>{summaryText(confirmedRun)}</Text>
          <Link href={routes.agentRun(confirmedRun.trace_id)} style={styles.linkButton}>
            查看 Agent Run 详情
          </Link>
        </CardBase>
      ) : null}
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  actions: {
    gap: 10,
    marginTop: 14
  },
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
  generated: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
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
  modeRow: {
    gap: 8,
    marginTop: 8
  },
  multiline: {
    minHeight: 110,
    textAlignVertical: "top"
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
