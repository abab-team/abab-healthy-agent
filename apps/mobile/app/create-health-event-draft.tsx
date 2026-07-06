import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members } from "@/constants/mockData";

export default function CreateHealthEventDraftScreen() {
  const [memberId, setMemberId] = useState("mom");
  const [summary, setSummary] = useState("5 月20日复查，准备整理成健康事件草稿。");
  const [preview, setPreview] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  return (
    <AppScreen>
      <Text style={styles.title}>创建健康事件草稿</Text>
      <SafetyNotice text="此页面只模拟 medical_event_draft_create，不会创建正式健康事件。" />
      <CardBase>
        <SectionHeader title="选择成员" />
        <View style={styles.row}>
          {members.map((member) => (
            <Pressable key={member.id} onPress={() => setMemberId(member.id)} style={styles.chip}>
              <StatusBadge label={member.name} tone={member.id === memberId ? "mint" : "plain"} />
            </Pressable>
          ))}
        </View>
        <TextInput value={summary} onChangeText={setSummary} multiline style={styles.input} />
        <Pressable style={styles.button} onPress={() => setPreview(true)}>
          <Text style={styles.buttonText}>生成草稿预览</Text>
        </Pressable>
      </CardBase>
      {preview ? (
        <CardBase>
          <SectionHeader title="confirmation=false 预览" />
          <Text style={styles.text}>{summary}</Text>
          <Pressable
            style={[styles.button, styles.secondaryButton]}
            onPress={() => {
              setConfirmed(true);
              Alert.alert("Mock 草稿已创建", "当前不请求后端，也不会创建正式健康事件。");
            }}
          >
            <Text style={styles.buttonText}>确认创建草稿</Text>
          </Pressable>
          {confirmed ? <StatusBadge label="confirmation=true mock 已完成" tone="mint" /> : null}
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
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    lineHeight: 22,
    marginVertical: 12,
    minHeight: 100,
    padding: 12,
    textAlignVertical: "top"
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    paddingVertical: 12
  },
  secondaryButton: {
    marginVertical: 12
  },
  buttonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "800",
    textAlign: "center"
  },
  text: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
  }
});
