import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";
import type { AgentRunResponse } from "@/types/api";

type Task = NonNullable<AgentRunResponse["conversation_task"]>;
const labels: Record<string, string> = { symptom: "症状记录", metric: "健康指标", medical_event: "健康事件", alert: "普通健康提醒" };

export function PendingHealthDraftCard({ task, busy, onConfirm, onCancel }: { task: Task; busy?: boolean; onConfirm: () => void; onCancel: () => void }) {
  const draft = task.draft;
  if (!draft) return null;
  const confirmed = task.status === "confirmed";
  const cancelled = task.status === "cancelled";
  return <View style={styles.card}>
    <View style={styles.heading}><Ionicons color={theme.colors.primary} name="clipboard-outline" size={21} /><View><Text style={styles.title}>{confirmed ? "已保存的记录" : cancelled ? "已取消的记录" : "待确认记录"}</Text><Text style={styles.caption}>{confirmed ? "已写入健康档案" : cancelled ? "不会写入健康档案" : "确认后才会写入正式健康档案"}</Text></View></View>
    <View style={styles.section}><Text style={styles.label}>本次记录内容</Text><Text style={styles.quote}>“{draft.raw_description ?? draft.details ?? draft.summary}”</Text></View>
    <View style={styles.section}><Text style={styles.label}>AI 整理结果</Text><Text style={styles.item}>• 记录类型：{labels[draft.candidate_type] ?? "健康记录"}</Text><Text style={styles.item}>• 内容：{draft.summary}</Text>{draft.occurred_at_hint ? <Text style={styles.item}>• 时间：{draft.occurred_at_hint}</Text> : null}{draft.duration_hint ? <Text style={styles.item}>• 持续：{draft.duration_hint}</Text> : null}</View>
    <View style={styles.section}><Text style={styles.label}>保存位置</Text><Text style={styles.item}>⌑ {draft.destination ?? "健康档案"}</Text></View>
    {!confirmed && !cancelled ? <View style={styles.actions}><Pressable disabled={busy} onPress={onCancel} style={styles.cancel}><Text style={styles.cancelText}>取消</Text></Pressable><Pressable disabled={busy} onPress={onConfirm} style={styles.confirm}><Text style={styles.confirmText}>{busy ? "正在保存…" : "确认记录"}</Text></Pressable></View> : null}
  </View>;
}

const styles = StyleSheet.create({
  actions: { flexDirection: "row", gap: 10, marginTop: 4 },
  cancel: { alignItems: "center", borderColor: theme.colors.primary, borderRadius: theme.radius.pill, borderWidth: 1, flex: 1, paddingVertical: 10 },
  cancelText: { color: theme.colors.primaryDark, fontSize: 13, fontWeight: "900" },
  caption: { color: theme.colors.subtle, fontSize: 11, marginTop: 1 },
  card: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, gap: 11, padding: 14 },
  confirm: { alignItems: "center", backgroundColor: theme.colors.primary, borderRadius: theme.radius.pill, flex: 1, paddingVertical: 10 },
  confirmText: { color: "#FFFFFF", fontSize: 13, fontWeight: "900" },
  heading: { alignItems: "center", flexDirection: "row", gap: 9 },
  item: { color: theme.colors.ink, fontSize: 12, lineHeight: 18 },
  label: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  quote: { backgroundColor: theme.colors.tealSoft, borderRadius: theme.radius.sm, color: theme.colors.ink, fontSize: 12, lineHeight: 18, padding: 9 },
  section: { gap: 5 },
  title: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" }
});
