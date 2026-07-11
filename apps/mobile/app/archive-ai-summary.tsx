import { useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { InlineSafetyNotice } from "@/components/common/InlineSafetyNotice";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { AgentRunResponse } from "@/types/api";

export default function ArchiveAiSummaryScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [loading, setLoading] = useState(false);
  const [run, setRun] = useState<AgentRunResponse | null>(null);
  const [message, setMessage] = useState("尚未生成新的整理内容。");

  async function generateSummary() {
    setLoading(true);
    const result = await provider.runDailyHealthBrief(session.currentUserId);
    setLoading(false);
    if (result.ok && result.data) {
      setRun(result.data);
      setMessage("已整理系统内已有记录。");
    } else {
      setMessage(result.error?.message ?? "暂时无法生成整理内容，请稍后再试。");
    }
  }

  return (
    <AppScreen>
      <ArchiveSubHeader title="AI 整理" />
      <InlineSafetyNotice />
      <CardBase>
        <Text style={styles.title}>健康资料整理</Text>
        <Text style={styles.copy}>{run?.generated_content ?? "这里会汇总你已保存的健康指标、文档和重要事件，帮助你回顾记录。"}</Text>
        <StatusBadge label={loading ? "正在整理" : message} tone="plain" />
        <Pressable disabled={loading} onPress={generateSummary} style={[styles.button, loading ? styles.buttonDisabled : null]}>
          <Text style={styles.buttonText}>{loading ? "正在整理…" : "生成新的整理"}</Text>
        </Pressable>
      </CardBase>
      <CardBase>
        <Text style={styles.title}>已整理内容</Text>
        <Text style={styles.item}>健康简报 · 仅根据系统内记录生成</Text>
        <Text style={styles.item}>健康事件草稿 · 仍需用户确认</Text>
        <Text style={styles.item}>就医资料摘要 · 仅供日常整理</Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  button: { backgroundColor: theme.colors.primary, borderRadius: theme.radius.pill, marginTop: 16, paddingVertical: 12 },
  buttonDisabled: { opacity: 0.65 },
  buttonText: { color: "#FFFFFF", fontSize: 14, fontWeight: "900", textAlign: "center" },
  copy: { color: theme.colors.subtle, fontSize: 14, lineHeight: 22, marginBottom: 14, marginTop: 10 },
  item: { borderTopColor: theme.colors.line, borderTopWidth: 1, color: theme.colors.ink, fontSize: 14, fontWeight: "700", paddingVertical: 13 },
  title: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" }
});
