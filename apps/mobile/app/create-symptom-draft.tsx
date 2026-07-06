import { StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";

export default function CreateSymptomDraftScreen() {
  return (
    <AppScreen>
      <Text style={styles.title}>创建症状草稿</Text>
      <SafetyNotice text="此处仅展示 confirmation=false 到 confirmation=true 的确认流程；未确认前不会进入正式记录。" />

      <CardBase>
        <SectionHeader title="记录内容" />
        <TextInput
          editable={false}
          multiline
          style={styles.input}
          value="今天有些头痛和乏力，想先记录下来，稍后补充时间和持续情况。"
        />
      </CardBase>

      <CardBase>
        <SectionHeader title="草稿预览" />
        <Text style={styles.line}>Workflow：symptom_draft_create</Text>
        <Text style={styles.line}>confirmation=false：仅生成待确认草稿预览。</Text>
        <Text style={styles.line}>confirmation=true：用户确认后才会进入受控写入流程。</Text>
        <View style={styles.actions}>
          <StatusBadge label="确认保存草稿" tone="mint" />
          <StatusBadge label="继续编辑" tone="blue" />
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
  input: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 12,
    minHeight: 110,
    padding: 12,
    textAlignVertical: "top"
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
