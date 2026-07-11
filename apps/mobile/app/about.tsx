import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { SettingsListItem } from "@/components/common/SettingsListItem";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";

export default function AboutScreen() {
  return <AppScreen>
    <ArchiveSubHeader title="关于 App" />
    <CardBase style={styles.brandCard}><View style={styles.brandIcon}><Ionicons color="#FFFFFF" name="heart-outline" size={33} /></View><View style={styles.brandCopy}><Text style={styles.brandName}>Family Health Agent</Text><Text style={styles.brandText}>家庭健康记录本与私人健康记录整理助手</Text><Text style={styles.version}>版本 1.0.0</Text></View></CardBase>
    <CardBase style={styles.groupCard}><SettingsListItem description="了解产品定位与使用方式" icon="leaf-outline" title="产品介绍" /><View style={styles.safetyRow}><View style={styles.iconWrap}><Ionicons color={theme.colors.primaryDark} name="shield-checkmark-outline" size={19} /></View><View style={styles.safetyCopy}><Text style={styles.safetyTitle}>健康安全说明</Text><Text style={styles.safetyText}>AI 内容基于系统内已有记录整理，不替代医生判断。</Text></View></View><SettingsListItem description="问题反馈与使用帮助" icon="help-circle-outline" title="帮助与反馈" /><SettingsListItem description="后续完善" icon="document-text-outline" title="隐私政策" /><SettingsListItem description="后续完善" icon="receipt-outline" last title="开源许可" /></CardBase>
    <Text style={styles.copyright}>© 2026 Family Health Agent</Text>
  </AppScreen>;
}

const styles = StyleSheet.create({
  brandCard: { alignItems: "center", flexDirection: "row", gap: 14 },
  brandCopy: { flex: 1 },
  brandIcon: { alignItems: "center", backgroundColor: theme.colors.primary, borderRadius: 17, height: 66, justifyContent: "center", width: 66 },
  brandName: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  brandText: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 4 },
  copyright: { color: theme.colors.subtle, fontSize: 11, paddingBottom: 4, textAlign: "center" },
  groupCard: { paddingBottom: 0, paddingTop: 0 },
  iconWrap: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 12, height: 40, justifyContent: "center", width: 40 },
  safetyCopy: { flex: 1 },
  safetyRow: { alignItems: "center", backgroundColor: "#F1FBF7", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 11, paddingVertical: 13 },
  safetyText: { color: theme.colors.primaryDark, fontSize: 12, lineHeight: 18, marginTop: 3 },
  safetyTitle: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" },
  version: { color: theme.colors.primaryDark, fontSize: 11, fontWeight: "800", marginTop: 6 }
});
