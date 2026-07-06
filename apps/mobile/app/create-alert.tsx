import { useState } from "react";
import { Alert as NativeAlert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members } from "@/constants/mockData";
import { mockApi } from "@/lib/mockApi";
import type { Alert } from "@/types/api";

const reminderTypes = ["记录提醒", "复查提醒", "资料整理提醒"];

export default function CreateAlertScreen() {
  const [title, setTitle] = useState("爸爸今晚量血压");
  const [memberId, setMemberId] = useState("dad");
  const [reminderType, setReminderType] = useState(reminderTypes[0]);
  const [time, setTime] = useState("今天 20:30");
  const [preview, setPreview] = useState<Alert | null>(null);
  const [status, setStatus] = useState("等待预览");
  const [loading, setLoading] = useState(false);

  async function previewAlert() {
    setLoading(true);
    setStatus("正在生成 confirmation=false 预览...");
    const result = await mockApi.createAlertPreview({
      target_user_id: memberId,
      title,
      reminder_type: reminderType,
      scheduled_at: time
    });
    setLoading(false);
    if (result.ok && result.data) {
      setPreview(result.data);
      setStatus("提醒预览已生成，尚未创建。");
    }
  }

  async function confirmAlert() {
    if (!preview) {
      setStatus("请先预览提醒。");
      return;
    }
    setLoading(true);
    const result = await mockApi.createAlertConfirmed({
      target_user_id: memberId,
      title,
      reminder_type: reminderType,
      scheduled_at: time
    });
    setLoading(false);
    if (result.ok) {
      setStatus("普通健康提醒 mock 创建成功，未请求后端。");
      NativeAlert.alert("Mock 提醒创建成功", "这不是急救服务，也不会代替你联系医院或家人。");
    }
  }

  return (
    <AppScreen>
      <Text style={styles.title}>创建健康提醒</Text>
      <SafetyNotice text="提醒不是急救；系统不会代替你联系医院或家人。" />
      <StatusBadge label={loading ? "处理中" : status} tone="plain" />

      <CardBase>
        <SectionHeader title="提醒标题" />
        <TextInput value={title} onChangeText={setTitle} style={styles.input} />
      </CardBase>

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
        <SectionHeader title="提醒类型与时间" />
        <View style={styles.row}>
          {reminderTypes.map((type) => (
            <Pressable key={type} onPress={() => setReminderType(type)} style={styles.chip}>
              <StatusBadge label={type} tone={type === reminderType ? "orange" : "plain"} />
            </Pressable>
          ))}
        </View>
        <TextInput value={time} onChangeText={setTime} style={styles.input} />
        <Pressable style={styles.button} onPress={previewAlert}>
          <Text style={styles.buttonText}>预览提醒</Text>
        </Pressable>
      </CardBase>

      {preview ? (
        <CardBase>
          <SectionHeader title="confirmation=false 预览" />
          <Text style={styles.line}>Workflow：alert_create</Text>
          <Text style={styles.line}>标题：{preview.title}</Text>
          <Text style={styles.line}>类型：{preview.reminder_type}</Text>
          <Text style={styles.line}>时间：{preview.scheduled_at}</Text>
          <Pressable style={[styles.button, styles.confirmButton]} onPress={confirmAlert}>
            <Text style={styles.buttonText}>确认创建提醒</Text>
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
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    marginTop: 12,
    padding: 12
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
