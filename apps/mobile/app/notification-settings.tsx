import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { SettingsToggleRow } from "@/components/common/SettingsToggleRow";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";

export default function NotificationSettingsScreen() {
  const [healthReminder, setHealthReminder] = useState(true);
  const [organizeReminder, setOrganizeReminder] = useState(true);
  const [draftReminder, setDraftReminder] = useState(true);
  return <AppScreen>
    <ArchiveSubHeader title="通知设置" />
    <Text style={styles.sectionTitle}>应用内提醒</Text>
    <CardBase style={styles.card}>
      <SettingsToggleRow description="每日记录提醒、连续记录提醒等" icon="heart-circle-outline" onValueChange={setHealthReminder} title="健康记录提醒" value={healthReminder} />
      <SettingsToggleRow description="整理记录、上传资料等提醒" icon="folder-open-outline" onValueChange={setOrganizeReminder} title="资料整理提醒" value={organizeReminder} />
      <SettingsToggleRow description="提醒确认 AI 已生成的草稿" icon="clipboard-outline" last onValueChange={setDraftReminder} title="待确认记录提醒" value={draftReminder} />
    </CardBase>
    <CardBase style={styles.plannedCard}><Ionicons color={theme.colors.primaryDark} name="notifications-outline" size={23} /><View style={styles.plannedCopy}><Text style={styles.plannedTitle}>系统通知（后续支持）</Text><Text style={styles.plannedText}>系统通知能力将在后续版本支持，包括锁屏提醒与消息通知等。</Text></View></CardBase>
    <Text style={styles.note}>关闭提醒不会删除系统内已有记录，仍可在 App 内查看相关内容。</Text>
  </AppScreen>;
}

const styles = StyleSheet.create({
  card: { paddingBottom: 0, paddingTop: 0 },
  note: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, paddingHorizontal: 4 },
  plannedCard: { alignItems: "flex-start", backgroundColor: theme.colors.blueSoft, flexDirection: "row", gap: 12 },
  plannedCopy: { flex: 1 },
  plannedText: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, marginTop: 5 },
  plannedTitle: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" },
  sectionTitle: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 4 }
});
