import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { family } from "@/constants/mockData";

export default function InviteMemberScreen() {
  const [contact, setContact] = useState("demo_family_member@example.com");
  const [sent, setSent] = useState(false);

  return (
    <AppScreen>
      <Text style={styles.title}>邀请成员</Text>
      <SafetyNotice text="当前为演示邀请流程，不会发送真实短信、邮件或通知。" />
      <CardBase>
        <SectionHeader title="邀请信息" />
        <Text style={styles.label}>家庭：{family.name}</Text>
        <TextInput value={contact} onChangeText={setContact} style={styles.input} />
        <Pressable
          style={styles.button}
          onPress={() => {
            setSent(true);
            Alert.alert("演示邀请已生成", "当前不会发送真实邀请。");
          }}
        >
          <Text style={styles.buttonText}>生成邀请预览</Text>
        </Pressable>
        {sent ? <StatusBadge label="已生成演示邀请" tone="mint" /> : null}
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
  input: {
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    color: colors.text,
    marginVertical: 12,
    padding: 12
  },
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
