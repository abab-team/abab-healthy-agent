import { useMemo } from "react";
import { StyleSheet, Text, View } from "react-native";
import { buildMetricRows, HealthMetricsList } from "@/components/cards/HealthMetricsList";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { AppScreen } from "@/components/layout/AppScreen";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import { router } from "expo-router";

export default function ArchiveMetricsScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const resource = useApiResource(() => provider.getPersonalHealthMetrics(), [session.currentUserId, session.dataMode]);
  return <AppScreen><ArchiveSubHeader title="健康指标" />{resource.error ? <ApiErrorState message={resource.error} /> : null}{resource.data ? <HealthMetricsList onPress={(id) => router.push(routes.archiveMetric(id))} rows={buildMetricRows(resource.data.bloodPressure, resource.data.metrics)} /> : null}<View style={styles.notice}><Text style={styles.noticeText}>所有数据整理自系统内记录，可在对应指标详情页查看趋势与历史。</Text></View></AppScreen>;
}

const styles = StyleSheet.create({
  notice: { paddingHorizontal: 4 },
  noticeText: { color: "#71817E", fontSize: 11, lineHeight: 17 }
});
