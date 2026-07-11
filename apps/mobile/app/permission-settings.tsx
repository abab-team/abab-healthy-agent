import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { SettingsToggleRow } from "@/components/common/SettingsToggleRow";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";

type SharingPermission = {
  id: string;
  title: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
  enabled: boolean;
};

const initialPermissions: SharingPermission[] = [
  { id: "profile", title: "基础资料", description: "姓名、年龄、家庭关系等", icon: "person-outline", enabled: true },
  { id: "metrics", title: "健康指标", description: "睡眠、血压、体重、步数等", icon: "pulse-outline", enabled: true },
  { id: "records", title: "健康记录", description: "症状记录、健康事件等", icon: "heart-outline", enabled: false },
  { id: "documents", title: "医疗资料与就医历史", description: "报告、文档与就诊记录等", icon: "document-text-outline", enabled: false },
  { id: "ai", title: "AI 整理", description: "基于系统内资料生成的安全摘要", icon: "sparkles-outline", enabled: true }
];

export default function PermissionSettingsScreen() {
  const [permissions, setPermissions] = useState([...initialPermissions]);
  const [saveNote, setSaveNote] = useState<string | null>(null);
  function updatePermission(id: string, enabled: boolean) {
    setSaveNote(null);
    setPermissions((current) => current.map((permission) => permission.id === id ? { ...permission, enabled } : permission));
  }

  return <AppScreen>
    <ArchiveSubHeader title="家庭共享设置" />
    <Text style={styles.subtitle}>选择希望与家庭成员共享的健康资料范围。</Text>
    <CardBase>
      <Text style={styles.overline}>当前家庭</Text>
      <View style={styles.familyRow}><View style={styles.house}><Ionicons color={theme.colors.primaryDark} name="home-outline" size={25} /></View><View style={styles.familyCopy}><Text style={styles.familyName}>幸福一家</Text><Text style={styles.familyText}>3 位成员</Text></View></View>
      <View style={styles.people}><View style={styles.person}><Text style={styles.personAvatar}>👩🏻</Text><Text style={styles.personName}>Gala</Text><Text style={styles.personNote}>本人</Text></View><View style={styles.person}><Text style={styles.personAvatar}>👨🏻</Text><Text style={styles.personName}>爸爸</Text><Text style={styles.personNote}>家庭成员</Text></View><View style={styles.person}><Text style={styles.personAvatar}>👩🏻‍🦰</Text><Text style={styles.personName}>妈妈</Text><Text style={styles.personNote}>家庭成员</Text></View></View>
    </CardBase>
    <Text style={styles.sectionTitle}>共享内容</Text>
    <CardBase style={styles.permissionCard}>{permissions.map((permission, index) => <SettingsToggleRow key={permission.id} description={permission.description} icon={permission.icon} last={index === permissions.length - 1} onValueChange={(enabled) => updatePermission(permission.id, enabled)} title={permission.title} value={permission.enabled} />)}</CardBase>
    <Pressable onPress={() => setSaveNote("展示设置已更新；真实共享范围仍以服务端权限为准。")} style={styles.saveButton}><Text style={styles.saveText}>保存共享设置</Text></Pressable>
    {saveNote ? <Text style={styles.saveNote}>{saveNote}</Text> : null}
    <CardBase style={styles.notice}><Ionicons color="#C48721" name="shield-checkmark-outline" size={19} /><Text style={styles.noticeText}>医疗资料属于个人健康信息，请谨慎设置共享范围。真实访问仍需经过家庭权限检查。</Text></CardBase>
  </AppScreen>;
}

const styles = StyleSheet.create({
  familyCopy: { flex: 1 },
  familyName: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  familyRow: { alignItems: "center", flexDirection: "row", gap: 12, marginTop: 8 },
  familyText: { color: theme.colors.subtle, fontSize: 13, marginTop: 4 },
  house: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 14, height: 50, justifyContent: "center", width: 50 },
  notice: { alignItems: "flex-start", backgroundColor: "#FFF8E8", flexDirection: "row", gap: 8 },
  noticeText: { color: "#82651F", flex: 1, fontSize: 12, lineHeight: 19 },
  overline: { color: theme.colors.subtle, fontSize: 12, fontWeight: "800" },
  people: { flexDirection: "row", gap: 9, marginTop: 16 },
  person: { alignItems: "center", flex: 1 },
  personAvatar: { fontSize: 30 },
  personName: { color: theme.colors.ink, fontSize: 13, fontWeight: "800", marginTop: 4 },
  personNote: { color: theme.colors.subtle, fontSize: 11, marginTop: 2 },
  permissionCard: { paddingBottom: 0, paddingTop: 0 },
  saveButton: { alignItems: "center", backgroundColor: theme.colors.primary, borderRadius: theme.radius.pill, justifyContent: "center", minHeight: 51 },
  saveNote: { color: theme.colors.primaryDark, fontSize: 12, lineHeight: 18, textAlign: "center" },
  saveText: { color: "#FFFFFF", fontSize: 16, fontWeight: "900" },
  sectionTitle: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 3 },
  subtitle: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19, marginTop: -8 }
});
