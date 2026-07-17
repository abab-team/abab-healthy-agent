import { useCallback, useMemo, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";

function formatGeneratedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  return date.toLocaleString("zh-CN", { day: "numeric", hour: "2-digit", minute: "2-digit", month: "numeric" });
}

export default function HealthBriefScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const latest = useApiResource(() => provider.getLatestDailyHealthBrief(), [session.currentUserId, session.dataMode]);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const content = latest.data?.generated_content ?? null;

  const refreshBrief = useCallback(async () => {
    setRefreshing(true);
    setRefreshError(null);
    const result = await provider.runDailyHealthBrief(session.currentUserId);
    setRefreshing(false);
    if (!result.ok) {
      setRefreshError(result.error?.message ?? "健康小结暂时无法整理，请稍后再试。");
      return;
    }
    await latest.reload();
  }, [latest.reload, provider, session.currentUserId]);

  return (
    <AppScreen>
      <ArchiveSubHeader title="健康小结" />
      <View style={styles.intro}>
        <Text style={styles.title}>健康小结 🌱</Text>
        <Text style={styles.subtitle}>根据系统内最近 7 天的已记录信息整理</Text>
      </View>

      {latest.loading ? <Text style={styles.loading}>正在读取最近生成的小结...</Text> : null}
      {latest.error ? <ApiErrorState message={latest.error} /> : null}
      {refreshError ? <ApiErrorState message={refreshError} /> : null}

      {content ? (
        <CardBase style={styles.contentCard}>
          <Text style={styles.generatedAt}>最近生成：{formatGeneratedAt(latest.data?.generated_at ?? "")}</Text>
          <Text style={styles.content}>{content}</Text>
        </CardBase>
      ) : !latest.loading ? (
        <CardBase style={styles.emptyCard}>
          <Text style={styles.emptyTitle}>还没有健康小结</Text>
          <Text style={styles.emptyText}>生成后会在这里展示最近的健康记录整理。</Text>
        </CardBase>
      ) : null}

      <PrimaryButton disabled={refreshing} label={refreshing ? "正在更新..." : content ? "更新个人健康小结" : "生成个人健康小结"} onPress={refreshBrief} />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  content: { color: theme.colors.ink, fontSize: 15, lineHeight: 25 },
  contentCard: { gap: 12 },
  emptyCard: { backgroundColor: theme.colors.tealSoft, gap: 7 },
  emptyText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19 },
  emptyTitle: { color: theme.colors.primaryDark, fontSize: 16, fontWeight: "900" },
  generatedAt: { color: theme.colors.subtle, fontSize: 12 },
  intro: { gap: 5, marginTop: -4 },
  loading: { color: theme.colors.subtle, fontSize: 13 },
  subtitle: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19 },
  title: { color: theme.colors.ink, fontSize: 24, fontWeight: "900" }
});
