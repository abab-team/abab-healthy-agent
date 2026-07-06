import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
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
          <Text style={styles.userDescription}>用心记录每一天，守护家人健康</Text>
          <Text style={styles.userDescription}>当前家庭：{currentUser.familyName}</Text>
        </View>
      </CardBase>

      <CardBase>
        <Text style={styles.sectionTitle}>开发者调试</Text>
        <Text style={styles.source}>Data Mode：{session.dataMode}</Text>
        <Text style={styles.source}>API Base URL：{session.apiBaseUrl || "未配置，默认保持 mock"}</Text>
        <Text style={styles.source}>X-Current-User-Id：{session.currentUserId || "未配置"}</Text>
        <Text style={styles.source}>
          /health：{health.loading ? "检查中" : health.error ? `失败：${health.error}` : `${health.data?.status} · ${health.data?.service}`}
        </Text>
        <Pressable style={styles.button} onPress={() => void health.reload()}>
          <Text style={styles.buttonText}>刷新 /health</Text>
        </Pressable>
      </CardBase>

      {settingsGroups.map((group, index) => (
        <CardBase key={index}>
          {group.map((item) => (
            <Pressable key={item.title} onPress={() => Alert.alert("Mock 设置", `${item.title} 当前为静态占位。`)}>
              <SettingsListItem title={item.title} description={item.description} icon={item.icon as never} />
            </Pressable>
          ))}
        </CardBase>
      ))}

      <CardBase>
        <Text style={styles.sectionTitle}>数据来源</Text>
        {dataSources.map((source) => (
          <Text key={source} style={styles.source}>{source}</Text>
        ))}
      </CardBase>

      <CardBase>
        <Text style={styles.sectionTitle}>关于 App</Text>
        <Text style={styles.about}>
          本 App 用于家庭日常健康记录、整理与提醒，不提供医疗判断、具体用药方案或急救服务。
        </Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  about: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20
  },
  avatar: {
    fontSize: 54
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    marginTop: 10,
    paddingVertical: 10
  },
  buttonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "800",
    textAlign: "center"
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800",
    marginBottom: 8
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
