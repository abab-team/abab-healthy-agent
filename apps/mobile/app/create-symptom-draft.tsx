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

export default function CreateSymptomDraftScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId]);
  const members = useMemo(() => overview.data?.members ?? mockFamilyMembers(), [overview.data]);
  const [selectedUserId, setSelectedUserId] = useState(session.dataMode === "api" ? session.currentUserId : "me");
  const [description, setDescription] = useState("今天头部不适并有些乏力，想先记录下来，稍后补充时间和持续情况。");
  const [previewRun, setPreviewRun] = useState<AgentRunResponse | null>(null);
  const [confirmedRun, setConfirmedRun] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState("等待输入。");
  const [loading, setLoading] = useState(false);
  const selectedMember = members.find((member) => member.user_id === selectedUserId || member.id === selectedUserId) ?? members[0];
  const targetUserId = selectedMember?.user_id ?? session.currentUserId;
  const familyId = selectedMember?.family_id;

  async function generatePreview() {
    setLoading(true);
    setError(null);
    setMessage("正在请求 confirmation=false 预览；预览不会写入。");
    setPreviewRun(null);
    const result = await provider.createSymptomDraftPreview({
      description,
      familyId,
      targetDisplayName: selectedMember?.display_name,
      targetUserId
    });
    setLoading(false);
    if (result.ok && result.data) {
      setPreviewRun(result.data);
      setMessage(result.data.blocked ? "后端安全阻断，未写入草稿。" : "预览已返回，尚未写入。");
      return;
    }
    const errorMessage = result.error?.message ?? "预览失败，请检查权限或网络。";
    setError(errorMessage);
    setMessage(errorMessage);
  }

  async function confirmDraft() {
    if (!previewRun) {
      setMessage("请先生成预览。");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage("正在请求 confirmation=true；成功后创建待确认草稿。");
    const result = await provider.createSymptomDraftConfirmed({
      description,
      familyId,
      targetDisplayName: selectedMember?.display_name,
      targetUserId
    });
    setLoading(false);
    if (result.ok && result.data) {
      setConfirmedRun(result.data);
      setMessage(result.data.blocked ? "后端阻断，未创建草稿。" : "待确认症状草稿已由后端创建。");
      return;
    }
    const errorMessage = result.error?.message ?? "确认失败，请检查权限或网络。";
    setError(errorMessage);
    setMessage(errorMessage);
  }

  return (
    <AppScreen>
      <Text style={styles.title}>创建症状草稿</Text>
      <SafetyNotice text="只整理你输入的健康记录，不能替代医生建议；如有紧急情况请联系医生或当地急救服务。" />
      <View style={styles.modeRow}>
        <ApiModeBadge mode={session.dataMode} label={session.dataMode === "api" ? "API Agent workflow" : "Mock 静态预览"} />
        <StatusBadge label={loading ? "处理中" : message} tone="plain" />
      </View>
      {error ? <ApiErrorState message={error} /> : null}
      {overview.error ? <ApiErrorState message={overview.error} /> : null}

      <WorkflowStatusCard
        confirmText="确认后创建待确认症状草稿"
        mode={session.dataMode}
        workflowType="symptom_draft_create"
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
        <SectionHeader title="记录内容" />
        <TextInput
          multiline
          style={styles.input}
          value={description}
          onChangeText={setDescription}
          placeholder="输入你想整理成草稿的健康记录"
        />
        <Pressable style={styles.button} onPress={generatePreview}>
          <Text style={styles.buttonText}>生成草稿预览</Text>
        </Pressable>
      </CardBase>

      {previewRun ? (
        <>
          <SafeResultSummary
            note="预览结果仅用于确认前检查，不写入正式数据。"
            run={previewRun}
            title={previewRun.blocked ? "安全阻断" : "预览结果"}
          />
          <CardBase>
            <SectionHeader title="确认下一步" />
            <Text style={styles.line}>确认后创建待确认症状草稿，仍不会生成正式健康事实。</Text>
            <Pressable style={[styles.button, styles.confirmButton]} onPress={confirmDraft}>
              <Text style={styles.buttonText}>确认创建草稿</Text>
            </Pressable>
          </CardBase>
        </>
      ) : null}

      {confirmedRun ? (
        <SafeResultSummary
          note="确认成功后只创建待确认草稿，正式确认入库留到后续流程。"
          run={confirmedRun}
          title={confirmedRun.blocked ? "未创建草稿" : "确认结果"}
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
  generated: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
  },
  input: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 12,
    minHeight: 116,
    padding: 12,
    textAlignVertical: "top"
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
