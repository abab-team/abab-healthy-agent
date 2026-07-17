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

export default function JoinFamilyScreen() {
  const session = useDemoSession(); const provider = getDataProvider(session.currentUserId);
  const [code, setCode] = useState(""); const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  async function submit() { const value = code.trim().toUpperCase(); if (!value) { setError("请输入邀请码。"); return; } setLoading(true); setError(null); const result = await provider.joinFamilyByCode(value); setLoading(false); if (!result.ok || !result.data) { setError(result.error?.message ?? "邀请码不可用。"); return; } router.replace(routes.familySharingSettings); }
  return <AppScreen><Text style={styles.title}>加入家庭</Text><Text style={styles.subtitle}>输入家人分享的邀请码。加入后默认不共享你的健康档案。</Text><Text style={styles.label}>邀请码</Text><TextInput autoCapitalize="characters" autoFocus maxLength={8} onChangeText={setCode} placeholder="例如：AB12CD34" placeholderTextColor={theme.colors.subtle} style={styles.input} value={code} /><PrimaryButton disabled={loading} label={loading ? "正在加入..." : "加入家庭"} onPress={submit} />{error ? <ApiErrorState message={error} /> : null}</AppScreen>;
}
const styles = StyleSheet.create({ input: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.sm, borderWidth: 1, color: theme.colors.ink, fontSize: 18, fontWeight: "900", letterSpacing: 2, marginBottom: 18, padding: 14 }, label: { color: theme.colors.ink, fontSize: 14, fontWeight: "800", marginBottom: 8, marginTop: 24 }, subtitle: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20 }, title: { color: theme.colors.ink, fontSize: 24, fontWeight: "900", marginTop: 8 } });
