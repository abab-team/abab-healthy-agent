import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { currentUser } from "@/constants/mockData";

const details = [
  ["昵称", "Gala", "person-outline"],
  ["性别", "女", "female-outline"],
  ["出生日期", "1995-05-14", "calendar-outline"],
  ["身高", "165 cm", "resize-outline"],
  ["体重", "58.0 kg", "scale-outline"]
] as const;

export default function ProfileScreen() {
  const [editing, setEditing] = useState(false);
  return <AppScreen>
    <ArchiveSubHeader title="个人资料" />
    <CardBase style={styles.profileCard}>
      <View style={styles.avatar}><Text style={styles.avatarText}>👩🏻</Text></View>
      <View style={styles.profileCopy}><View style={styles.nameRow}><Text style={styles.name}>{currentUser.name}</Text><StatusBadge label="当前用户" tone="mint" /></View><Text style={styles.description}>记录每一天，守护家人的健康生活。</Text></View>
    </CardBase>
    <CardBase style={styles.groupCard}>
      <View style={styles.headingRow}><Text style={styles.heading}>基础资料</Text><Pressable onPress={() => setEditing((value) => !value)}><Text style={styles.edit}>{editing ? "完成" : "编辑"}</Text></Pressable></View>
      {details.map(([label, value, icon], index) => <View key={label} style={[styles.row, index === details.length - 1 ? styles.lastRow : null]}><View style={styles.iconWrap}><Ionicons color={theme.colors.primary} name={icon} size={18} /></View><Text style={styles.label}>{label}</Text><Text style={styles.value}>{value}</Text><Ionicons color={theme.colors.subtle} name="chevron-forward" size={16} /></View>)}
    </CardBase>
    <CardBase style={styles.groupCard}>
      <Text style={styles.heading}>健康档案关联</Text>
      <View style={styles.infoRow}><Ionicons color={theme.colors.primary} name="home-outline" size={19} /><View style={styles.infoCopy}><Text style={styles.label}>当前家庭</Text><Text style={styles.value}>幸福一家</Text></View></View>
      <View style={styles.infoRow}><Ionicons color={theme.colors.primary} name="people-outline" size={19} /><View style={styles.infoCopy}><Text style={styles.label}>家庭身份</Text><Text style={styles.value}>本人（女儿）</Text></View></View>
      <View style={[styles.infoRow, styles.lastInfo]}><Ionicons color={theme.colors.primary} name="share-social-outline" size={19} /><View style={styles.infoCopy}><Text style={styles.label}>共享状态</Text><Text style={styles.value}>部分内容共享</Text></View></View>
    </CardBase>
    <Text style={styles.note}>基础资料用于个人档案展示与家庭共享范围识别。</Text>
  </AppScreen>;
}

const styles = StyleSheet.create({
  avatar: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 34, height: 68, justifyContent: "center", width: 68 },
  avatarText: { fontSize: 40 },
  description: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19, marginTop: 5 },
  edit: { color: theme.colors.primaryDark, fontSize: 13, fontWeight: "900" },
  groupCard: { paddingBottom: 0, paddingTop: 13 },
  heading: { color: theme.colors.ink, fontSize: 17, fontWeight: "900" },
  headingRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", paddingBottom: 4 },
  iconWrap: { alignItems: "center", backgroundColor: theme.colors.coralSoft, borderRadius: 10, height: 33, justifyContent: "center", width: 33 },
  infoCopy: { flex: 1, flexDirection: "row", justifyContent: "space-between" },
  infoRow: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 10, paddingVertical: 13 },
  label: { color: theme.colors.subtle, fontSize: 13 },
  lastInfo: { borderBottomWidth: 0 },
  lastRow: { borderBottomWidth: 0 },
  name: { color: theme.colors.ink, fontSize: 20, fontWeight: "900" },
  nameRow: { alignItems: "center", flexDirection: "row", flexWrap: "wrap", gap: 8 },
  note: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, paddingHorizontal: 4 },
  profileCard: { alignItems: "center", backgroundColor: theme.colors.blueSoft, flexDirection: "row", gap: 14 },
  profileCopy: { flex: 1 },
  row: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 10, paddingVertical: 12 },
  value: { color: theme.colors.ink, fontSize: 13, fontWeight: "700", marginLeft: "auto" }
});
