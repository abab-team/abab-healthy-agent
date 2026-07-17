import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function RegisterScreen() {
  const auth = useAuthSession();
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function submit() {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) {
      setMessage("请输入邮箱和密码。");
      return;
    }
    if (password.length < 8) {
      setMessage("密码至少需要 8 个字符。");
      return;
    }
    if (password !== confirmPassword) {
      setMessage("两次输入的密码不一致。");
      return;
    }

    setMessage(null);
    try {
      await auth.register(normalizedEmail, password, nickname.trim() || undefined);
    } catch {
      // The hook preserves a safe server error message for display below.
    }
  }

  return (
    <AppScreen>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>家庭健康管家</Text>
        <Text style={styles.title}>创建你的账号</Text>
        <Text style={styles.subtitle}>用一个账号安全地保存自己的健康记录，并按权限与家人共享。</Text>
      </View>
      <CardBase style={styles.card}>
        <Text style={styles.label}>昵称（选填）</Text>
        <TextInput autoComplete="name" onChangeText={setNickname} placeholder="例如：小林" style={styles.input} textContentType="name" value={nickname} />
        <Text style={styles.label}>邮箱</Text>
        <TextInput autoCapitalize="none" autoComplete="email" keyboardType="email-address" onChangeText={setEmail} placeholder="name@example.com" style={styles.input} textContentType="emailAddress" value={email} />
        <Text style={styles.label}>密码</Text>
        <TextInput autoComplete="new-password" onChangeText={setPassword} placeholder="至少 8 个字符" secureTextEntry style={styles.input} textContentType="newPassword" value={password} />
        <Text style={styles.label}>确认密码</Text>
        <TextInput autoComplete="new-password" onChangeText={setConfirmPassword} placeholder="请再次输入密码" secureTextEntry style={styles.input} textContentType="newPassword" value={confirmPassword} />
        <Pressable disabled={auth.loading} onPress={submit} style={[styles.button, auth.loading && styles.buttonDisabled]}><Text style={styles.buttonText}>{auth.loading ? "创建中..." : "创建账号"}</Text></Pressable>
        {message || auth.error ? <Text accessibilityLiveRegion="polite" style={styles.message}>{message ?? auth.error}</Text> : null}
        <View style={styles.footerRow}><Text style={styles.footerText}>已有账号？</Text><Pressable onPress={() => router.replace("/login")}><Text style={styles.link}>去登录</Text></Pressable></View>
      </CardBase>
      <SafetyNotice text="创建账号不会自动获得家人的健康数据访问权限；共享范围仍由家庭权限设置控制。" />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  button: { backgroundColor: colors.primary, borderRadius: 12, marginTop: 8, paddingVertical: 13 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontSize: 15, fontWeight: "900", textAlign: "center" },
  card: { gap: 8 },
  eyebrow: { color: colors.primaryDark, fontSize: 13, fontWeight: "900", letterSpacing: 1 },
  footerRow: { alignItems: "center", flexDirection: "row", gap: 4, justifyContent: "center", marginTop: 10 },
  footerText: { color: colors.textMuted, fontSize: 13 },
  hero: { gap: 6, paddingTop: 16 },
  input: { backgroundColor: colors.surfaceSoft, borderColor: colors.border, borderRadius: 12, borderWidth: 1, color: colors.text, fontSize: 15, paddingHorizontal: 12, paddingVertical: 11 },
  label: { color: colors.text, fontSize: 14, fontWeight: "800" },
  link: { color: colors.primaryDark, fontSize: 13, fontWeight: "900" },
  message: { color: colors.textMuted, fontSize: 13, lineHeight: 20, marginTop: 4 },
  subtitle: { color: colors.textMuted, fontSize: 14, lineHeight: 21 },
  title: { color: colors.text, fontSize: 28, fontWeight: "900" }
});
