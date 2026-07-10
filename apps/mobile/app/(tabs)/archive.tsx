import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { TrendCard } from "@/components/cards/TrendCard";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { Period, PeriodSelector } from "@/components/common/PeriodSelector";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { ArchiveTrends } from "@/types/api";

const timeline = [
  { date: "05-14", detail: "7.2 小时", icon: "moon-outline", title: "睡眠记录" },
  { date: "05-13", detail: "118/76 mmHg", icon: "pulse-outline", title: "血压记录" },
  { date: "05-12", detail: "62.2 kg", icon: "scale-outline", title: "体重记录" },
  { date: "05-11", detail: "轻微头痛，已保存为记录草稿", icon: "create-outline", title: "症状记录" },
  { date: "05-10", detail: "复查相关事项已整理", icon: "calendar-outline", title: "健康事件" },
  { date: "05-09", detail: "年度体检报告", icon: "document-text-outline", title: "文档上传" }
] as const;

export default function ArchiveScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const [period, setPeriod] = useState<Period>("30天");
  const [trends, setTrends] = useState<ArchiveTrends | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    provider.getArchiveTrends().then((result) => {
      if (!active) return;
      if (result.ok && result.data) {
        setTrends(result.data);
        setError(null);
      } else {
        setError(result.error?.message ?? "健康档案暂时无法加载。");
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [provider]);

  const preferredTrendSeries = ["sleep_duration", "blood_pressure", "weight"]
    .map((metricType) => trends?.series.find((series) => series.metric_type === metricType))
    .filter((series): series is NonNullable<typeof series> => Boolean(series));

  return (
    <AppScreen>
      <ScreenHeader subtitle="长期记录、趋势与重要健康资料。" title="健康档案" trailing={<StatusBadge label="个人档案" tone="mint" />} />

      <CardBase style={styles.trendSection}>
        <View style={styles.trendHeading}>
          <View>
            <Text style={styles.sectionTitle}>长期趋势</Text>
            <Text style={styles.sectionCaption}>基于系统内已有记录整理，不作医学判断。</Text>
          </View>
          {loading ? <Text style={styles.loading}>加载中</Text> : null}
        </View>
        <PeriodSelector onChange={setPeriod} value={period} />
        {error ? <ApiErrorState message={error} /> : null}
        <View style={styles.trendCards}>
          {preferredTrendSeries.map((series) => <TrendCard key={series.metric_type} series={series} />)}
        </View>
        {!loading && !error && preferredTrendSeries.length === 0 ? <Text style={styles.empty}>系统内暂无趋势记录。</Text> : null}
      </CardBase>

      <View style={styles.timelineHeading}>
        <View>
          <Text style={styles.sectionTitle}>健康时间轴</Text>
          <Text style={styles.sectionCaption}>把个人健康记录按时间串联起来。</Text>
        </View>
        <Text style={styles.allRecords}>查看全部记录</Text>
      </View>
      <View style={styles.timeline}>
        {timeline.map((item, index) => (
          <View key={`${item.date}-${item.title}`} style={styles.timelineItem}>
            <View style={styles.timelineRail}>
              <View style={[styles.timelineDot, index === 0 ? styles.timelineDotActive : null]}>
                <Ionicons color="#FFFFFF" name={item.icon} size={10} />
              </View>
              {index < timeline.length - 1 ? <View style={styles.timelineLine} /> : null}
            </View>
            <View style={styles.timelineCopy}>
              <Text style={styles.timelineDate}>{item.date}</Text>
              <Text style={styles.timelineTitle}>{item.title}</Text>
              <Text style={styles.timelineDetail}>{item.detail}</Text>
            </View>
          </View>
        ))}
      </View>

      <Link href={routes.documents} style={styles.documentCard}>
        <View style={styles.documentIcon}><Ionicons color={theme.colors.primaryDark} name="document-text-outline" size={24} /></View>
        <View style={styles.documentCopy}>
          <Text style={styles.documentTitle}>体检报告与文档</Text>
          <Text style={styles.documentNote}>查看个人资料与安全摘要预览。</Text>
        </View>
        <Ionicons color={theme.colors.subtle} name="chevron-forward" size={20} />
      </Link>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  allRecords: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  documentCard: { alignItems: "center", backgroundColor: theme.colors.blueSoft, borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, color: theme.colors.ink, flexDirection: "row", gap: 12, padding: 15 },
  documentCopy: { flex: 1 },
  documentIcon: { alignItems: "center", backgroundColor: "#FFFFFF", borderRadius: 14, height: 46, justifyContent: "center", width: 46 },
  documentNote: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 4 },
  documentTitle: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" },
  empty: { color: theme.colors.subtle, fontSize: 13, paddingVertical: 10 },
  loading: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "800" },
  sectionCaption: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 4 },
  sectionTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" },
  timeline: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, padding: 16 },
  timelineCopy: { flex: 1, paddingBottom: 13 },
  timelineDate: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  timelineDetail: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 3 },
  timelineDot: { alignItems: "center", backgroundColor: "#7A9CEC", borderRadius: 9, height: 18, justifyContent: "center", width: 18 },
  timelineDotActive: { backgroundColor: theme.colors.primary },
  timelineHeading: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", marginTop: 4 },
  timelineItem: { flexDirection: "row", gap: 12 },
  timelineLine: { backgroundColor: theme.colors.line, flex: 1, marginVertical: 4, width: 2 },
  timelineRail: { alignItems: "center", width: 18 },
  timelineTitle: { color: theme.colors.ink, fontSize: 14, fontWeight: "800", marginTop: 3 },
  trendCards: { gap: 10, marginTop: 2 },
  trendHeading: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  trendSection: { gap: 14 }
});
