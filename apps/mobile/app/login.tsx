import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { router } from "expo-router";
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
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function submit() {
    setMessage(null);
    try {
      await auth.login(email.trim(), password);
      setMessage("登录成功，已保存本地会话摘要。");
      // Navigate by the public route. Addressing the route group here causes
      // React Navigation to look for a literal "(tabs)" screen on Android.
      router.replace("/settings");
    } catch {
      setMessage("登录失败，请检查账号、密码和 API Base URL。");
    }
  }

  return (
    <AppScreen>
      <Text style={styles.title}>登录</Text>
      <Text style={styles.subtitle}>用于 api-auth mode 的最小登录入口。</Text>

      <CardBase style={styles.card}>
        <View style={styles.badges}>
          <ApiModeBadge mode={dataMode} />
          <Text style={styles.mode}>{authMode === "auth" ? "Authorization Bearer" : "Demo Header"}</Text>
        </View>
        <Text style={styles.label}>邮箱</Text>
        <TextInput
          autoCapitalize="none"
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="demo@example.com"
          style={styles.input}
          value={email}
        />
        <Text style={styles.label}>密码</Text>
        <TextInput
          onChangeText={setPassword}
          placeholder="请输入密码"
          secureTextEntry
          style={styles.input}
          value={password}
        />
        <Pressable disabled={auth.loading} onPress={submit} style={[styles.button, auth.loading && styles.buttonDisabled]}>
          <Text style={styles.buttonText}>{auth.loading ? "登录中..." : "登录"}</Text>
        </Pressable>
        {message || auth.error ? <Text style={styles.message}>{message ?? auth.error}</Text> : null}
      </CardBase>

      <SafetyNotice text="登录态只用于识别当前用户和维护会话，不改变家庭共享权限、Agent Safety 或 Tool Executor 边界。" />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  badges: {
    alignItems: "center",
    flexDirection: "row",
    gap: 8,
    marginBottom: 8
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    marginTop: 8,
    paddingVertical: 13
  },
  buttonDisabled: {
    opacity: 0.6
  },
  buttonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "900",
    textAlign: "center"
  },
  card: {
    gap: 8
  },
  input: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    color: colors.text,
    fontSize: 15,
    paddingHorizontal: 12,
    paddingVertical: 11
  },
  label: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "800"
  },
  message: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20
  },
  mode: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: "800"
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 20
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  }
});
