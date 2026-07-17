import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";

export default function InviteMemberScreen() {
  const { code, familyName } = useLocalSearchParams<{ code?: string; familyName?: string }>();
  const [copied, setCopied] = useState(false);

  return (
    <AppScreen>
      <Text style={styles.title}>邀请码已生成</Text>
      <SafetyNotice text="邀请码 7 天内有效且仅可使用一次。家人加入后，仍由各自决定健康信息共享范围。" />
      <CardBase>
        <SectionHeader title="邀请信息" />
        <Text style={styles.label}>家庭：{familyName ?? "你的家庭"}</Text>
        <Text style={styles.code}>{code ?? "请从家庭页重新生成邀请码"}</Text>
        <Pressable
          style={styles.button}
          onPress={() => {
            setCopied(true);
          }}
        >
          <Text style={styles.buttonText}>我已分享给家人</Text>
        </Pressable>
        {copied ? <StatusBadge label="等待家人输入邀请码加入" tone="mint" /> : null}
      </CardBase>
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
  label: {
    color: colors.textMuted,
    fontSize: 14,
    marginTop: 12
  },
  code: { color: colors.primaryDark, fontSize: 25, fontWeight: "900", letterSpacing: 3, marginVertical: 18, textAlign: "center" },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    paddingVertical: 12
  },
  buttonText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "800",
    textAlign: "center"
  }
});
