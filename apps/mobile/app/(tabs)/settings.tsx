import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { BackendStatusCard } from "@/components/common/BackendStatusCard";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { SettingsListItem } from "@/components/common/SettingsListItem";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { currentUser, dataSources } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

export default function SettingsScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const health = useApiResource(() => Promise.resolve(provider.getHealthStatus()), [session.currentUserId, session.dataMode]);
  const [moreOpen, setMoreOpen] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);
  const authenticatedUser = session.authSession.user;

  function confirmLogout() {
    Alert.alert("退出登录", "退出后将清除本设备保存的会话信息。", [
      { style: "cancel", text: "取消" },
      { onPress: () => void session.authSession.logout(), style: "destructive", text: "退出登录" }
    ]);
  }

  return <AppScreen>
    <ScreenHeader subtitle="管理你的账户、家庭与数据。" title="我的" />
    <CardBase style={styles.profileCard}>
      <View style={styles.avatar}><Text style={styles.avatarText}>👩🏻</Text></View>
      <View style={styles.profileCopy}><View style={styles.nameRow}><Text style={styles.name}>{authenticatedUser?.nickname ?? currentUser.name}</Text><StatusBadge label={session.isAuthenticated ? "已登录" : "演示用户"} tone="mint" /></View><Text style={styles.profileText}>{authenticatedUser?.email ?? "记录每一天，守护家人的健康生活。"}</Text><Text style={styles.familyText}>当前家庭：{currentUser.familyName}</Text></View>
    </CardBase>

    <CardBase style={styles.groupCard}>
      <SettingsListItem description="管理个人信息与健康档案关联" icon="person-outline" onPress={() => router.push(routes.profile)} title="个人资料" />
      <SettingsListItem description="管理应用内的记录与整理提醒" icon="notifications-outline" last onPress={() => router.push(routes.notificationSettings)} title="通知设置" />
    </CardBase>
    {session.authMode === "auth" ? <CardBase style={styles.groupCard}>
      <SettingsListItem description="安全退出当前设备，已保存的会话信息将被清除" icon="log-out-outline" last onPress={confirmLogout} title="退出登录" />
    </CardBase> : null}
    <CardBase style={styles.groupCard}>
      <SettingsListItem description="管理家庭成员与共享范围" icon="people-outline" onPress={() => router.push(routes.familySharingSettings)} title="家庭共享设置" />
      <SettingsListItem description="隐私与数据保护选项" icon="shield-checkmark-outline" onPress={() => router.push(routes.privacySettings)} title="隐私设置" />
      <SettingsListItem description="查看或删除可编辑的对话偏好记忆" icon="sparkles-outline" last onPress={() => router.push(routes.agentMemory)} title="AI 记忆管理" />
    </CardBase>
    <CardBase style={styles.groupCard}>
      <SettingsListItem description="版本信息、帮助与健康安全说明" icon="information-circle-outline" last onPress={() => router.push(routes.about)} title="关于 App" />
    </CardBase>

    <CardBase style={styles.moreCard}>
      <Pressable onPress={() => setMoreOpen((value) => !value)} style={styles.moreHeader}><View><Text style={styles.sectionTitle}>更多与开发</Text><Text style={styles.note}>数据来源、本地连接与开发调试</Text></View><Ionicons color={theme.colors.primaryDark} name={moreOpen ? "chevron-up" : "chevron-down"} size={20} /></Pressable>
      {moreOpen ? <View style={styles.moreContent}>
        <View><Text style={styles.subTitle}>数据来源</Text>{dataSources.map((source) => <Text key={source} style={styles.source}>• {source}</Text>)}</View>
        <Pressable onPress={() => setDebugOpen((value) => !value)} style={styles.debugHeader}><View><Text style={styles.subTitle}>开发者调试</Text><Text style={styles.note}>用于本地联调的连接与身份信息。</Text></View><StatusBadge label={debugOpen ? "收起" : "展开"} tone="plain" /></Pressable>
        {debugOpen ? <View style={styles.debugContent}><BackendStatusCard accessTokenPreview={session.authSession.accessTokenPreview} apiBaseUrl={session.apiBaseUrl} authMode={session.authMode} currentUserId={session.currentUserId} health={health.data} healthError={health.error} loading={health.loading} mode={session.dataMode} onRefresh={() => void health.reload()} warnings={session.warnings} /></View> : null}
      </View> : null}
    </CardBase>
    <Text style={styles.footerNote}>家庭健康管家用于日常健康记录、整理与提醒。AI 内容基于系统内记录，不替代医生判断。</Text>
  </AppScreen>;
}

const styles = StyleSheet.create({
  avatar: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 28, height: 58, justifyContent: "center", width: 58 },
  avatarText: { fontSize: 35 },
  debugContent: { gap: 12 },
  debugHeader: { alignItems: "center", borderTopColor: theme.colors.line, borderTopWidth: 1, flexDirection: "row", justifyContent: "space-between", paddingTop: 14 },
  familyText: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "800", marginTop: 4 },
  footerNote: { color: theme.colors.subtle, fontSize: 11, lineHeight: 18, paddingHorizontal: 4 },
  groupCard: { paddingBottom: 0, paddingTop: 0 },
  moreCard: { backgroundColor: "#F4FAF7" },
  moreContent: { gap: 15, marginTop: 15 },
  moreHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  name: { color: theme.colors.ink, fontSize: 20, fontWeight: "900" },
  nameRow: { alignItems: "center", flexDirection: "row", flexWrap: "wrap", gap: 8 },
  note: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 4 },
  profileCard: { alignItems: "center", backgroundColor: theme.colors.blueSoft, flexDirection: "row", gap: 14 },
  profileCopy: { flex: 1 },
  profileText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19, marginTop: 6 },
  sectionTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" },
  source: { color: theme.colors.subtle, fontSize: 12, lineHeight: 20 },
  subTitle: { color: theme.colors.ink, fontSize: 14, fontWeight: "900" }
});
