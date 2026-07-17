import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, TextInput } from "react-native";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

export default function CreateFamilyScreen() {
  const session = useDemoSession(); const provider = getDataProvider(session.currentUserId);
  const [name, setName] = useState(""); const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  async function submit() { if (!name.trim()) { setError("请输入家庭名称。"); return; } setLoading(true); setError(null); const result = await provider.createFamily({ name: name.trim(), ownerDisplayName: session.authSession.user?.nickname ?? "我" }); setLoading(false); if (!result.ok || !result.data) { setError(result.error?.message ?? "创建家庭失败。"); return; } router.replace({ pathname: "/invite-member", params: { code: result.data.invitation.invite_code, familyName: result.data.family.name } }); }
  return <AppScreen><Text style={styles.title}>创建家庭</Text><Text style={styles.subtitle}>为家人建立一个共同的健康空间。健康资料默认不会共享。</Text><Text style={styles.label}>家庭名称</Text><TextInput autoFocus maxLength={100} onChangeText={setName} placeholder="例如：幸福一家" placeholderTextColor={theme.colors.subtle} style={styles.input} value={name} /><PrimaryButton disabled={loading} label={loading ? "正在创建..." : "创建并生成邀请码"} onPress={submit} />{error ? <ApiErrorState message={error} /> : null}</AppScreen>;
}
const styles = StyleSheet.create({ input: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.sm, borderWidth: 1, color: theme.colors.ink, fontSize: 16, marginBottom: 18, padding: 14 }, label: { color: theme.colors.ink, fontSize: 14, fontWeight: "800", marginBottom: 8, marginTop: 24 }, subtitle: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20 }, title: { color: theme.colors.ink, fontSize: 24, fontWeight: "900", marginTop: 8 } });
