import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members } from "@/constants/mockData";
import { mockApi } from "@/lib/mockApi";
import type { HealthRecordDraft } from "@/types/api";

export default function CreateSymptomDraftScreen() {
  const [memberId, setMemberId] = useState("me");
  const [description, setDescription] = useState("今天有些头痛和乏力，想先记录下来，稍后补充时间和持续情况。");
  const [preview, setPreview] = useState<HealthRecordDraft | null>(null);
  const [status, setStatus] = useState("等待输入");
  const [loading, setLoading] = useState(false);

  async function generatePreview() {
    setLoading(true);
    setStatus("正在生成 confirmation=false 预览...");
    const result = await mockApi.createSymptomDraftPreview({ target_user_id: memberId, description });
    setLoading(false);
    if (result.ok && result.data) {
      setPreview(result.data);
      setStatus("草稿预览已生成，尚未写入。");
    }
  }

  async function confirmDraft() {
    if (!preview) {
      setStatus("请先生成草稿预览。");
      return;
    }
    setLoading(true);
    const result = await mockApi.createSymptomDraftConfirmed({ target_user_id: memberId, description });
    setLoading(false);
    if (result.ok) {
      setStatus("confirmation=true mock 已完成，未请求后端。");
      Alert.alert("Mock 草稿创建成功", "当前只模拟交互，不会写入真实数据。");
    }
  }

  return (
    <AppScreen>
      <Text style={styles.title}>创建症状草稿</Text>
      <SafetyNotice text="AI 只整理系统内记录和你的描述；不做诊断。如有紧急不适请联系医生或当地急救服务。" />
      <StatusBadge label={loading ? "处理中" : status} tone="plain" />

      <CardBase>
        <SectionHeader title="选择成员" />
        <View style={styles.row}>
          {members.map((member) => (
            <Pressable key={member.id} onPress={() => setMemberId(member.id)} style={styles.chip}>
              <StatusBadge label={member.name} tone={member.id === memberId ? "mint" : "plain"} />
            </Pressable>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="症状描述" />
        <TextInput
          multiline
          style={styles.input}
          value={description}
          onChangeText={setDescription}
          placeholder="输入你想记录的症状描述"
        />
        <Pressable style={styles.button} onPress={generatePreview}>
          <Text style={styles.buttonText}>生成草稿预览</Text>
        </Pressable>
      </CardBase>

      {preview ? (
        <CardBase>
          <SectionHeader title="confirmation=false 预览" />
          <Text style={styles.line}>Workflow：symptom_draft_create</Text>
          <Text style={styles.line}>标题：{preview.title}</Text>
          <Text style={styles.line}>摘要：{preview.summary}</Text>
          <Text style={styles.line}>预览不会写入；确认后才进入受控草稿创建流程。</Text>
          <Pressable style={[styles.button, styles.confirmButton]} onPress={confirmDraft}>
            <Text style={styles.buttonText}>确认创建草稿</Text>
          </Pressable>
        </CardBase>
      ) : null}
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
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  chip: {
    marginRight: 4
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
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    marginTop: 14,
    paddingVertical: 12
  },
  confirmButton: {
    backgroundColor: colors.primaryDark
  },
  buttonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "800",
    textAlign: "center"
  },
  line: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
  }
});
