import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { AgentMemoryItem } from "@/types/api";

export default function AgentMemoryScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [items, setItems] = useState<AgentMemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadMemory() {
    setLoading(true);
    setError(null);
    const result = await provider.listAgentMemory();
    setLoading(false);
    if (result.ok && result.data) {
      setItems(result.data);
    } else {
      setError(result.error?.message ?? "AI 记忆加载失败。");
    }
  }

  async function deleteMemory(id: string) {
    const result = await provider.deleteAgentMemory(id);
    if (result.ok) {
      setItems((current) => current.filter((item) => item.id !== id));
    } else {
      setError(result.error?.message ?? "删除失败，请稍后再试。");
    }
  }

  useEffect(() => {
    void loadMemory();
  }, [session.currentUserId, session.dataMode]);

  return (
    <AppScreen>
      <Pressable style={styles.backButton} onPress={() => router.back()}>
        <Ionicons name="chevron-back" size={20} color={colors.primaryDark} />
        <Text style={styles.backText}>返回</Text>
      </Pressable>

      <Text style={styles.title}>AI 记忆管理</Text>
      <Text style={styles.subtitle}>只保存安全偏好和对话上下文摘要，不保存未经确认的医疗事实。</Text>

      <CardBase>
        <View style={styles.headerRow}>
          <Text style={styles.sectionTitle}>长期偏好记忆</Text>
          <StatusBadge label={session.dataMode === "api" ? "API 数据" : "演示数据"} tone="mint" />
        </View>
        <Text style={styles.description}>你可以删除不想继续使用的偏好。删除后，后续对话不会再参考该条记忆。</Text>
        {loading ? <Text style={styles.description}>正在加载...</Text> : null}
        {error ? <ApiErrorState message={error} /> : null}
        {!loading && items.length === 0 ? <Text style={styles.description}>系统内暂无安全偏好记忆。</Text> : null}
        <View style={styles.memoryList}>
          {items.map((item) => (
            <View key={item.id} style={styles.memoryItem}>
              <View style={styles.memoryCopy}>
                <Text style={styles.memoryType}>{item.memory_type}</Text>
                <Text style={styles.memoryContent}>{item.content}</Text>
                <Text style={styles.memoryMeta}>置信度 {item.confidence} · 来源 {item.source}</Text>
              </View>
              {item.is_user_editable ? (
                <Pressable style={styles.deleteButton} onPress={() => void deleteMemory(item.id)}>
                  <Text style={styles.deleteText}>删除</Text>
                </Pressable>
              ) : null}
            </View>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <Text style={styles.sectionTitle}>安全边界</Text>
        <Text style={styles.description}>AI 记忆不是正式健康事实来源，也不会替代医生判断。</Text>
        <Text style={styles.description}>系统不会把诊断、处方、剂量、停药建议或未确认健康结论写入长期记忆。</Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  backButton: {
    alignItems: "center",
    flexDirection: "row",
    gap: 4,
    paddingTop: 6
  },
  backText: {
    color: colors.primaryDark,
    fontSize: 14,
    fontWeight: "800"
  },
  deleteButton: {
    borderColor: colors.warning,
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8
  },
  deleteText: {
    color: colors.warning,
    fontSize: 12,
    fontWeight: "900"
  },
  description: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 6
  },
  headerRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  memoryContent: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
    marginTop: 4
  },
  memoryCopy: {
    flex: 1
  },
  memoryItem: {
    alignItems: "center",
    backgroundColor: colors.surfaceSoft,
    borderRadius: 14,
    flexDirection: "row",
    gap: 10,
    padding: 12
  },
  memoryList: {
    gap: 10,
    marginTop: 12
  },
  memoryMeta: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 6
  },
  memoryType: {
    color: colors.primaryDark,
    fontSize: 12,
    fontWeight: "900"
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "900"
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 6
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    marginTop: 10
  }
});
