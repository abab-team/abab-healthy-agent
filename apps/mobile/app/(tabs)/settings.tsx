import { router } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { BackendStatusCard } from "@/components/common/BackendStatusCard";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { SettingsListItem } from "@/components/common/SettingsListItem";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { currentUser, dataSources, settingsGroups } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

export default function SettingsScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const health = useApiResource(() => Promise.resolve(provider.getHealthStatus()), [session.currentUserId, session.dataMode]);
  const [debugOpen, setDebugOpen] = useState(false);
  const userGroups = settingsGroups.filter((group) => !group.some((item) => item.icon === "construct-outline"));

  return (
    <AppScreen>
      <ScreenHeader subtitle="管理你的账户、家庭与数据。" title="我的" />

      <CardBase style={styles.profileCard}>
        <View style={styles.avatar}><Text style={styles.avatarText}>👩🏻</Text></View>
        <View style={styles.profileCopy}>
          <View style={styles.nameRow}>
            <Text style={styles.name}>{currentUser.name}</Text>
            <StatusBadge label="当前用户" tone="mint" />
          </View>
          <Text style={styles.profileText}>记录每一天，守护家人的健康生活。</Text>
          <Text style={styles.familyText}>当前家庭：{currentUser.familyName}</Text>
        </View>
      </CardBase>

      {userGroups.map((group, index) => (
        <CardBase key={index}>
          {group.map((item) => (
            <SettingsListItem description={item.description} icon={item.icon as never} key={item.title} title={item.title} />
          ))}
        </CardBase>
      ))}

      <CardBase>
        <Text style={styles.sectionTitle}>数据来源</Text>
        <View style={styles.sourceList}>
          {dataSources.map((source) => <Text key={source} style={styles.source}>• {source}</Text>)}
        </View>
        <Text style={styles.note}>文档处理与 OCR 摘要预览已接入；真实 OCR 服务与长期 RAG 索引仍在后续计划中。</Text>
      </CardBase>

      <CardBase>
        <Text style={styles.sectionTitle}>AI 记忆管理</Text>
        <Text style={styles.note}>查看或删除可编辑的对话偏好记忆；这里不会展示未经确认的医疗事实。</Text>
        <Pressable onPress={() => router.push(routes.agentMemory)} style={styles.outlineButton}>
          <Text style={styles.outlineText}>打开 AI 记忆管理</Text>
        </Pressable>
      </CardBase>

      <CardBase>
        <Pressable onPress={() => setDebugOpen((value) => !value)} style={styles.debugHeader}>
          <View>
            <Text style={styles.sectionTitle}>开发者调试</Text>
            <Text style={styles.note}>用于本地联调的连接与身份信息。</Text>
          </View>
          <StatusBadge label={debugOpen ? "收起" : "展开"} tone="plain" />
        </Pressable>
        {debugOpen ? (
          <View style={styles.debugContent}>
            <BackendStatusCard
              accessTokenPreview={session.authSession.accessTokenPreview}
              apiBaseUrl={session.apiBaseUrl}
              authMode={session.authMode}
              currentUserId={session.currentUserId}
              health={health.data}
              healthError={health.error}
              loading={health.loading}
              mode={session.dataMode}
              onRefresh={() => void health.reload()}
              warnings={session.warnings}
            />
            <View style={styles.debugPanel}>
              <Text style={styles.debugTitle}>受控 Agent 能力</Text>
              <Text style={styles.note}>健康简报、健康查询与确认后草稿流程已接入。系统不开放任意工具调用，也不接收 tool_name 或 input_data。</Text>
              <Text style={styles.note}>预览不会写入；确认后仅创建待确认草稿或普通健康提醒。</Text>
              <View style={styles.debugActions}>
                <Pressable onPress={() => router.push("/login")} style={styles.outlineButton}><Text style={styles.outlineText}>登录设置</Text></Pressable>
                <Pressable onPress={() => void session.authSession.logout()} style={styles.outlineButton}><Text style={styles.outlineText}>退出登录</Text></Pressable>
              </View>
            </View>
          </View>
        ) : null}
      </CardBase>

      <CardBase style={styles.safetyCard}>
        <Text style={styles.sectionTitle}>关于 App</Text>
        <Text style={styles.note}>家庭健康管家用于日常健康记录、整理与提醒。所有 AI 内容基于系统内记录，不替代医生判断。</Text>
        <Text style={styles.note}>真机联调请使用电脑局域网 IP；Expo Go 不能使用 localhost。</Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  avatar: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 28, height: 58, justifyContent: "center", width: 58 },
  avatarText: { fontSize: 35 },
  debugActions: { flexDirection: "row", flexWrap: "wrap", gap: 10, marginTop: 4 },
  debugContent: { gap: 12, marginTop: 14 },
  debugHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  debugPanel: { backgroundColor: theme.colors.canvas, borderRadius: theme.radius.sm, gap: 7, padding: 12 },
  debugTitle: { color: theme.colors.ink, fontSize: 14, fontWeight: "900" },
  familyText: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "800", marginTop: 3 },
  name: { color: theme.colors.ink, fontSize: 20, fontWeight: "900" },
  nameRow: { alignItems: "center", flexDirection: "row", flexWrap: "wrap", gap: 8 },
  note: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, marginTop: 5 },
  outlineButton: { borderColor: theme.colors.primary, borderRadius: theme.radius.pill, borderWidth: 1, paddingHorizontal: 14, paddingVertical: 9 },
  outlineText: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  profileCard: { alignItems: "center", backgroundColor: theme.colors.blueSoft, flexDirection: "row", gap: 14 },
  profileCopy: { flex: 1 },
  profileText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19, marginTop: 6 },
  safetyCard: { backgroundColor: theme.colors.tealSoft },
  sectionTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" },
  source: { color: theme.colors.subtle, fontSize: 13, lineHeight: 21 },
  sourceList: { marginTop: 6 }
});
