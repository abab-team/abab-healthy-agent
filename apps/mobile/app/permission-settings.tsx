import { Ionicons } from "@expo/vector-icons";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { SettingsToggleRow } from "@/components/common/SettingsToggleRow";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { FamilySharePermission } from "@/types/api";

const fields = [
  ["can_view_profile", "基础资料", "昵称、生日等基础信息", "person-outline"],
  ["can_view_metrics", "健康指标", "睡眠、血压、体重、步数等", "pulse-outline"],
  ["can_view_symptoms", "症状记录", "已记录的症状信息", "heart-outline"],
  ["can_view_medical_events", "健康事件", "就医和健康事件", "calendar-outline"],
  ["can_view_documents", "医疗资料", "报告与已上传资料", "document-text-outline"]
] as const;

export default function PermissionSettingsScreen() {
  const session = useDemoSession(); const provider = getDataProvider(session.currentUserId);
  const [familyId, setFamilyId] = useState<string | null>(null); const [value, setValue] = useState<FamilySharePermission | null>(null); const [error, setError] = useState<string | null>(null); const [saving, setSaving] = useState(false);
  useEffect(() => { let active = true; async function load() { const families = await provider.listMyFamilies(); const id = families.data?.[0]?.id; if (!id) { if (active) setError("请先创建或加入家庭。"); return; } const permission = await provider.getMyFamilySharePermission(id); if (!active) return; setFamilyId(id); if (permission.ok && permission.data) setValue(permission.data); else setError(permission.error?.message ?? "无法读取共享设置。"); } void load(); return () => { active = false; }; }, [session.currentUserId, session.dataMode]);
  async function save(updates: Partial<FamilySharePermission>) { if (!familyId || !value) return; setSaving(true); setError(null); const result = await provider.updateMyFamilySharePermission(familyId, updates); setSaving(false); if (result.ok && result.data) setValue(result.data); else setError(result.error?.message ?? "保存失败。"); }
  return <AppScreen><ArchiveSubHeader title="家庭共享设置" /><Text style={styles.subtitle}>只有你主动开启的内容，家人才可以在家庭中查看。</Text><CardBase><Text style={styles.title}>默认保持私密</Text><Text style={styles.copy}>加入家庭不会自动公开任何健康档案。保存后，家庭视图会按最新授权即时显示。</Text></CardBase><CardBase style={styles.permissionCard}>{fields.map(([key, title, description, icon], index) => <SettingsToggleRow key={key} description={description} icon={icon as keyof typeof Ionicons.glyphMap} last={index === fields.length - 1} onValueChange={(enabled) => void save({ [key]: enabled })} title={title} value={Boolean(value?.[key])} />)}</CardBase><Pressable disabled={saving || !value} onPress={() => void save({ share_all: !value?.share_all })} style={styles.saveButton}><Text style={styles.saveText}>{saving ? "正在保存..." : value?.share_all ? "关闭全部共享" : "开启全部共享"}</Text></Pressable>{error ? <ApiErrorState message={error} /> : null}</AppScreen>;
}
const styles = StyleSheet.create({ copy: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20, marginTop: 6 }, permissionCard: { paddingBottom: 0, paddingTop: 0 }, saveButton: { alignItems: "center", backgroundColor: theme.colors.primary, borderRadius: theme.radius.pill, justifyContent: "center", minHeight: 51 }, saveText: { color: "#FFFFFF", fontSize: 15, fontWeight: "900" }, subtitle: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20, marginTop: -8 }, title: { color: theme.colors.ink, fontSize: 16, fontWeight: "900" } });
