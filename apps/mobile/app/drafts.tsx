import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { pendingDrafts } from "@/constants/mockData";
import { mockApi } from "@/lib/mockApi";
import type { DraftStatus } from "@/types/api";

const statusLabel: Record<DraftStatus, string> = {
  pending: "待确认",
  confirmed: "已确认",
  later: "稍后处理"
};

export default function DraftsScreen() {
  const [drafts, setDrafts] = useState(
    pendingDrafts.map((draft) => ({ ...draft, status: "pending" as DraftStatus, editing: false }))
  );
  const [message, setMessage] = useState("当前为静态 mock，不会请求后端。");
  const [loadingId, setLoadingId] = useState<string | null>(null);

  async function updateStatus(id: string, status: DraftStatus) {
    setLoadingId(id);
    setMessage("正在模拟提交...");
    const result = await mockApi.updateDraftStatus(id, status);
    setLoadingId(null);
    if (!result.ok) {
      setMessage("mock 更新失败，请稍后再试。");
      return;
    }
    setDrafts((current) => current.map((draft) => (draft.id === id ? { ...draft, status, editing: false } : draft)));
    setMessage(status === "confirmed" ? "草稿已 mock 确认。" : "草稿已标记为稍后处理。");
  }

  return (
    <AppScreen>
      <Text style={styles.title}>待确认草稿</Text>
      <SafetyNotice text="草稿确认后才会进入正式记录；当前为静态 mock，不是真实提交。" />
      <StatusBadge label={message} tone="plain" />

      {drafts.map((draft) => (
        <CardBase key={draft.id}>
          <View style={styles.draftHeader}>
            <View>
              <Text style={styles.draftType}>{draft.type}</Text>
              <Text style={styles.draftTitle}>{draft.title}</Text>
            </View>
            <StatusBadge label={loadingId === draft.id ? "处理中" : statusLabel[draft.status]} tone={draft.status === "confirmed" ? "mint" : "purple"} />
          </View>
          <Text style={styles.meta}>创建于 {draft.createdAt}</Text>
          {draft.editing ? (
            <TextInput value={draft.summary} multiline style={styles.input} />
          ) : (
            <Text style={styles.summary}>{draft.summary}</Text>
          )}
          <View style={styles.actions}>
            <Pressable style={styles.button} onPress={() => updateStatus(draft.id, "confirmed")}>
              <Text style={styles.buttonText}>确认</Text>
            </Pressable>
            <Pressable
              style={[styles.button, styles.secondaryButton]}
              onPress={() => {
                setDrafts((current) => current.map((item) => (item.id === draft.id ? { ...item, editing: true } : item)));
                Alert.alert("Mock 编辑", "这里展示编辑区域，不会保存到后端。");
              }}
            >
              <Text style={styles.secondaryText}>修改</Text>
            </Pressable>
            <Pressable style={[styles.button, styles.lightButton]} onPress={() => updateStatus(draft.id, "later")}>
              <Text style={styles.lightText}>暂不处理</Text>
            </Pressable>
          </View>
        </CardBase>
      ))}
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
  draftHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  draftType: {
    color: colors.primaryDark,
    fontSize: 13,
    fontWeight: "800"
  },
  draftTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "900",
    marginTop: 4
  },
  meta: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 8
  },
  summary: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10
  },
  input: {
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    lineHeight: 22,
    marginTop: 10,
    minHeight: 82,
    padding: 12,
    textAlignVertical: "top"
  },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 14
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10
  },
  secondaryButton: {
    backgroundColor: colors.blue
  },
  lightButton: {
    backgroundColor: colors.orange
  },
  buttonText: {
    color: "#fff",
    fontWeight: "800"
  },
  secondaryText: {
    color: colors.primaryDark,
    fontWeight: "800"
  },
  lightText: {
    color: colors.warning,
    fontWeight: "800"
  }
});
