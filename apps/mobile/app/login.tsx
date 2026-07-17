import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { router, type Href } from "expo-router";
import { CardBase } from "@/components/cards/CardBase";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { authMode, dataMode } from "@/lib/apiConfig";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function LoginScreen() {
  const auth = useAuthSession();
  const [email, setEmail] = useState("gala.demo@example.com");
  const [password, setPassword] = useState("123456");
  const [message, setMessage] = useState<string | null>(null);

  async function submit() {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) {
      setMessage("请输入邮箱和密码。");
      return;
    }

    setMessage(null);
    try {
      await auth.login(normalizedEmail, password);
      router.replace("/");
    } catch {
      // The hook preserves a safe server error message for display below.
    }
  }

  return (
    <AppScreen>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>家庭健康管家</Text>
        <Text style={styles.title}>欢迎回来</Text>
        <Text style={styles.subtitle}>登录后可查看并管理属于你的健康记录与家庭共享内容。</Text>
      </View>

      <CardBase style={styles.card}>
        <View style={styles.badges}>
          <ApiModeBadge mode={dataMode} />
          <Text style={styles.mode}>{authMode === "auth" ? "安全登录" : "演示模式"}</Text>
        </View>
        <Text style={styles.label}>邮箱</Text>
        <TextInput
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="name@example.com"
          style={styles.input}
          textContentType="emailAddress"
          value={email}
        />
        <Text style={styles.label}>密码</Text>
        <TextInput
          autoComplete="password"
          onChangeText={setPassword}
          placeholder="请输入密码"
          secureTextEntry
          style={styles.input}
          textContentType="password"
          value={password}
        />
        <Pressable disabled={auth.loading} onPress={submit} style={[styles.button, auth.loading && styles.buttonDisabled]}>
          <Text style={styles.buttonText}>{auth.loading ? "登录中..." : "登录"}</Text>
        </Pressable>
        {message || auth.error ? <Text accessibilityLiveRegion="polite" style={styles.message}>{message ?? auth.error}</Text> : null}
        <View style={styles.footerRow}>
          <Text style={styles.footerText}>还没有账号？</Text>
          <Pressable onPress={() => router.push("/register" as Href)}><Text style={styles.link}>创建账号</Text></Pressable>
        </View>
      </CardBase>

      <SafetyNotice text="登录只用于识别当前用户和维护会话，不会改变家庭共享权限或 Agent 的安全边界。" />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  badges: { alignItems: "center", flexDirection: "row", gap: 8, marginBottom: 8 },
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
  mode: { color: colors.textMuted, fontSize: 13, fontWeight: "800" },
  subtitle: { color: colors.textMuted, fontSize: 14, lineHeight: 21 },
  title: { color: colors.text, fontSize: 28, fontWeight: "900" }
});
