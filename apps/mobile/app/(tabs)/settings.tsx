import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { BackendStatusCard } from "@/components/common/BackendStatusCard";
import { CardBase } from "@/components/cards/CardBase";
import { SettingsListItem } from "@/components/common/SettingsListItem";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { currentUser, dataSources, settingsGroups } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";

export default function SettingsScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const health = useApiResource(() => Promise.resolve(provider.getHealthStatus()), [session.currentUserId, session.dataMode]);

  const userGroups = settingsGroups.filter((group) => !group.some((item) => item.title === "开发者调试"));

  return (
    <AppScreen>
      <Text style={styles.title}>设置</Text>

      <CardBase style={styles.userCard}>
        <Text style={styles.avatar}>👩🏻</Text>
        <View style={styles.userCopy}>
          <View style={styles.userTitle}>
            <Text style={styles.userName}>{currentUser.name}</Text>
            <StatusBadge label={currentUser.badge} tone="mint" />
          </View>
          <Text style={styles.userDescription}>用心记录每一天，守护家人健康。</Text>
          <Text style={styles.userDescription}>当前家庭：{currentUser.familyName}</Text>
        </View>
      </CardBase>

      {userGroups.map((group, index) => (
        <CardBase key={index}>
          {group.map((item) => (
            <Pressable key={item.title} onPress={() => Alert.alert("演示设置", `${item.title} 当前为演示入口。`)}>
              <SettingsListItem title={item.title} description={item.description} icon={item.icon as never} />
            </Pressable>
          ))}
        </CardBase>
      ))}

      <CardBase>
        <Text style={styles.sectionTitle}>数据来源</Text>
        {dataSources.map((source) => (
          <Text key={source} style={styles.source}>
            {source}
          </Text>
        ))}
        <Text style={styles.about}>文档处理与 OCR preview 已接入；真实 OCR provider 仍未实现。</Text>
        <Text style={styles.about}>RAG 当前为后端 / Agent 内部增强，移动端暂无独立 RAG 页面。</Text>
      </CardBase>

      <CardBase>
        <Text style={styles.sectionTitle}>关于 App</Text>
        <Text style={styles.about}>
          本 App 用于家庭日常健康记录、整理与提醒，不提供医疗判断、具体用药方案或急救服务。
        </Text>
      </CardBase>

      <Text style={styles.debugHeading}>开发者调试</Text>

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

      <CardBase>
        <Text style={styles.sectionTitle}>登录态</Text>
        <Text style={styles.about}>
          当前模式：{session.authMode === "auth" ? "api-auth / Bearer token" : "api-demo / X-Current-User-Id"}
        </Text>
        <Text style={styles.about}>
          当前用户：{session.authSession.user?.nickname ?? session.authSession.user?.email ?? currentUser.name}
        </Text>
        <Text style={styles.about}>Access Token：{session.authSession.accessTokenPreview}</Text>
        <Text style={styles.about}>
          Refresh Token：{session.authSession.refreshTokenStored ? "已安全保存摘要，不展示完整 token" : "未保存"}
        </Text>
        <View style={styles.actions}>
          <Pressable style={styles.secondaryButton} onPress={() => router.push("/login")}>
            <Text style={styles.secondaryButtonText}>打开登录页</Text>
          </Pressable>
          <Pressable style={styles.secondaryButton} onPress={() => void session.authSession.logout()}>
            <Text style={styles.secondaryButtonText}>退出登录</Text>
          </Pressable>
        </View>
      </CardBase>

      <CardBase>
        <Text style={styles.sectionTitle}>Agent API 状态</Text>
        <View style={styles.badgeWrap}>
          <StatusBadge label="daily_health_brief 已接入" tone="mint" />
          <StatusBadge label="symptom_draft_create 已接入" tone="mint" />
          <StatusBadge label="medical_event_draft_create 已接入" tone="mint" />
          <StatusBadge label="alert_create 已接入" tone="mint" />
        </View>
        <Text style={styles.about}>预览不会写入，确认后只会创建待确认草稿或普通健康提醒。</Text>
        <Text style={styles.about}>草稿正式确认入库仍未完整接入移动端。</Text>
        <Text style={styles.about}>LangGraph 尚未实现。</Text>
        <Text style={styles.about}>真实 OCR provider、RAG 持久化索引、embedding/vector DB 仍未实现。</Text>
      </CardBase>

      <CardBase>
        <Text style={styles.sectionTitle}>真机访问提示</Text>
        <Text style={styles.about}>Web 本机调试可以使用 localhost。</Text>
        <Text style={styles.about}>Expo Go 真机不能使用 localhost，需要配置电脑局域网 IP。</Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  about: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 4
  },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 10
  },
  avatar: {
    fontSize: 54
  },
  badgeWrap: {
    alignItems: "flex-start",
    gap: 8,
    marginBottom: 6
  },
  debugHeading: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "900",
    marginTop: 4
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800",
    marginBottom: 8
  },
  secondaryButton: {
    borderColor: colors.primary,
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 9
  },
  secondaryButtonText: {
    color: colors.primaryDark,
    fontSize: 13,
    fontWeight: "900"
  },
  source: {
    color: colors.textMuted,
    fontSize: 14,
    paddingVertical: 6
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  },
  userCard: {
    alignItems: "center",
    flexDirection: "row",
    gap: 14
  },
  userCopy: {
    flex: 1,
    gap: 4
  },
  userDescription: {
    color: colors.textMuted,
    fontSize: 13
  },
  userName: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "900"
  },
  userTitle: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  }
});
