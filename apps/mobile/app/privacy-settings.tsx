import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { SettingsListItem } from "@/components/common/SettingsListItem";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { routes } from "@/lib/routes";

export default function PrivacySettingsScreen() {
  return <AppScreen>
    <ArchiveSubHeader title="隐私设置" />
    <Text style={styles.sectionTitle}>数据可见范围</Text>
    <CardBase style={styles.groupCard}><SettingsListItem description="在“家庭共享设置”中查看或调整" icon="eye-outline" last onPress={() => router.push(routes.familySharingSettings)} title="查看与管理共享范围" /></CardBase>
    <Text style={styles.sectionTitle}>账号安全</Text>
    <CardBase style={styles.groupCard}><SettingsListItem description="当前为正常使用中" icon="person-circle-outline" title="账号状态" /><View style={styles.plannedRow}><View style={styles.iconDanger}><Ionicons color="#D95A5A" name="trash-outline" size={20} /></View><View style={styles.copy}><Text style={styles.dangerTitle}>删除账号</Text><Text style={styles.description}>该功能仍在规划中，当前不会执行删除操作。</Text></View><Text style={styles.planned}>功能规划中</Text></View></CardBase>
    <Text style={styles.sectionTitle}>数据管理</Text>
    <CardBase style={styles.groupCard}><View style={styles.plannedRow}><View style={styles.iconInfo}><Ionicons color="#5367B9" name="download-outline" size={20} /></View><View style={styles.copy}><Text style={styles.title}>导出我的数据</Text><Text style={styles.description}>该功能仍在规划中，当前不提供下载能力。</Text></View><Text style={styles.planned}>功能规划中</Text></View></CardBase>
    <CardBase style={styles.notice}><Ionicons color={theme.colors.primaryDark} name="lock-closed-outline" size={19} /><Text style={styles.noticeText}>系统仅在您已授权的范围内展示家庭健康资料。</Text></CardBase>
  </AppScreen>;
}

const styles = StyleSheet.create({
  copy: { flex: 1 },
  dangerTitle: { color: "#D95A5A", fontSize: 15, fontWeight: "900" },
  description: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 3 },
  groupCard: { paddingBottom: 0, paddingTop: 0 },
  iconDanger: { alignItems: "center", backgroundColor: "#FFF0F0", borderRadius: 12, height: 40, justifyContent: "center", width: 40 },
  iconInfo: { alignItems: "center", backgroundColor: "#EEF1FF", borderRadius: 12, height: 40, justifyContent: "center", width: 40 },
  notice: { alignItems: "center", backgroundColor: "#F2FAF7", flexDirection: "row", gap: 9 },
  noticeText: { color: theme.colors.primaryDark, flex: 1, fontSize: 12, lineHeight: 19 },
  planned: { color: "#6670B8", fontSize: 11, fontWeight: "800" },
  plannedRow: { alignItems: "center", borderTopColor: theme.colors.line, borderTopWidth: 1, flexDirection: "row", gap: 11, paddingVertical: 14 },
  sectionTitle: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 4 },
  title: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" }
});
