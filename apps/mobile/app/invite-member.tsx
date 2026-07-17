import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";

export default function InviteMemberScreen() {
  const { code: initialCode, familyName } = useLocalSearchParams<{ code?: string; familyName?: string }>();
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const [code, setCode] = useState(initialCode);
  const [copied, setCopied] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generateInvitationCode() {
    setGenerating(true);
    setError(null);
    const families = await provider.listMyFamilies();
    if (!families.ok || !families.data?.[0]) {
      setGenerating(false);
      setError(families.error?.message ?? "未找到可邀请成员的家庭。");
      return;
    }
    const result = await provider.createFamilyInvitationCode(families.data[0].id);
    setGenerating(false);
    if (!result.ok || !result.data) {
      setError(result.error?.message ?? "生成邀请码失败。");
      return;
    }
    setCode(result.data.invite_code);
    setCopied(false);
  }

  return (
    <AppScreen>
      <Text style={styles.title}>{code ? "邀请码已生成" : "邀请家庭成员"}</Text>
      <SafetyNotice text="邀请码 7 天内有效且仅可使用一次。家人加入后，仍由各自决定健康信息共享范围。" />
      <CardBase>
        <SectionHeader title="邀请信息" />
        <Text style={styles.label}>家庭：{familyName ?? "你的家庭"}</Text>
        {code ? <Text style={styles.code}>{code}</Text> : <Text style={styles.hint}>生成后可将 8 位邀请码分享给家人。</Text>}
        {code ? (
          <PrimaryButton label="我已分享给家人" onPress={() => setCopied(true)} />
        ) : (
          <PrimaryButton disabled={generating} label={generating ? "正在生成..." : "生成邀请码"} onPress={() => void generateInvitationCode()} />
        )}
        {copied ? <StatusBadge label="等待家人输入邀请码加入" tone="mint" /> : null}
      </CardBase>
      {error ? <ApiErrorState message={error} /> : null}
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  title: { color: colors.text, fontSize: 24, fontWeight: "900", paddingTop: 8 },
  label: { color: colors.textMuted, fontSize: 14, marginTop: 12 },
  hint: { color: colors.textMuted, fontSize: 15, lineHeight: 22, marginVertical: 18, textAlign: "center" },
  code: { color: colors.primaryDark, fontSize: 25, fontWeight: "900", letterSpacing: 3, marginVertical: 18, textAlign: "center" }
});
