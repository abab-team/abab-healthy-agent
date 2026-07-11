import { Ionicons } from "@expo/vector-icons";
import { useEffect, useMemo, useState } from "react";
import { Alert, Pressable, StyleSheet, Switch, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { AgentMemoryItem } from "@/types/api";

export default function AgentMemoryScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [items, setItems] = useState<AgentMemoryItem[]>([]);
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadMemory() {
    setLoading(true); setError(null);
    const result = await provider.listAgentMemory();
    setLoading(false);
    if (result.ok && result.data) setItems(result.data); else setError(result.error?.message ?? "AI 记忆加载失败。");
  }

  function toggleMemory(value: boolean) {
    if (value) { setEnabled(true); return; }
    Alert.alert("关闭 AI 记忆", "关闭后，当前 App 不会在后续对话中使用这些偏好。已保存的偏好不会被删除。", [{ text: "取消", style: "cancel" }, { text: "确认关闭", onPress: () => setEnabled(false) }]);
  }

  function deleteMemory(item: AgentMemoryItem) {
    Alert.alert("删除此条偏好", "删除后将无法恢复。", [{ text: "取消", style: "cancel" }, { text: "删除", style: "destructive", onPress: () => void provider.deleteAgentMemory(item.id).then((result) => result.ok ? setItems((current) => current.filter((entry) => entry.id !== item.id)) : setError(result.error?.message ?? "删除失败，请稍后再试。")) }]);
  }

  useEffect(() => { void loadMemory(); }, [session.currentUserId, session.dataMode]);
  const preferences = useMemo(() => items.filter((item) => item.is_user_editable), [items]);

  return <AppScreen>
    <ArchiveSubHeader title="AI 记忆管理" />
    <CardBase style={styles.infoCard}><View style={styles.infoIcon}><Ionicons color={theme.colors.primaryDark} name="sparkles-outline" size={23} /></View><View style={styles.infoCopy}><Text style={styles.infoTitle}>AI 记忆说明</Text><Text style={styles.infoText}>AI 记忆只用于对话偏好与交互习惯，不会保存未经确认的医疗事实或原始健康记录。</Text></View></CardBase>
    <CardBase style={styles.switchCard}><Text style={styles.switchTitle}>允许 AI 使用我的对话偏好</Text><Switch onValueChange={toggleMemory} thumbColor="#FFFFFF" trackColor={{ false: "#D8E1DE", true: theme.colors.primary }} value={enabled} /></CardBase>
    <Text style={styles.sectionTitle}>已保存的偏好</Text>
    <CardBase style={styles.listCard}>
      {loading ? <Text style={styles.empty}>正在加载...</Text> : null}
      {error ? <ApiErrorState message={error} /> : null}
      {!loading && !error && preferences.length === 0 ? <View style={styles.emptyWrap}><Ionicons color={theme.colors.subtle} name="sparkles-outline" size={26} /><Text style={styles.empty}>暂未保存偏好</Text><Text style={styles.emptyNote}>AI 会在对话中学习可编辑的偏好。</Text></View> : null}
      {preferences.map((item, index) => <View key={item.id} style={[styles.memoryRow, index === preferences.length - 1 ? styles.lastRow : null]}><Ionicons color={theme.colors.subtle} name="reorder-three-outline" size={20} /><Text numberOfLines={2} style={styles.memoryText}>{item.content}</Text><Pressable accessibilityLabel="删除偏好" hitSlop={8} onPress={() => deleteMemory(item)}><Ionicons color="#E06565" name="trash-outline" size={19} /></Pressable></View>)}
    </CardBase>
    <Text style={styles.note}>关闭记忆只影响当前 App 的偏好使用；删除会移除对应的可编辑偏好。</Text>
  </AppScreen>;
}

const styles = StyleSheet.create({
  empty: { color: theme.colors.subtle, fontSize: 13, textAlign: "center" },
  emptyNote: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, textAlign: "center" },
  emptyWrap: { alignItems: "center", gap: 7, paddingVertical: 20 },
  infoCard: { alignItems: "flex-start", backgroundColor: theme.colors.blueSoft, flexDirection: "row", gap: 12 },
  infoCopy: { flex: 1 },
  infoIcon: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 12, height: 42, justifyContent: "center", width: 42 },
  infoText: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, marginTop: 4 },
  infoTitle: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" },
  lastRow: { borderBottomWidth: 0 },
  listCard: { paddingBottom: 0, paddingTop: 0 },
  memoryRow: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 9, paddingVertical: 13 },
  memoryText: { color: theme.colors.ink, flex: 1, fontSize: 14, lineHeight: 20 },
  note: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, paddingHorizontal: 4 },
  sectionTitle: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 3 },
  switchCard: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  switchTitle: { color: theme.colors.ink, flex: 1, fontSize: 15, fontWeight: "900", paddingRight: 16 }
});
