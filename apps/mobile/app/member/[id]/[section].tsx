import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useMemo } from "react";
import { StyleSheet, Text, View } from "react-native";
import { ArchiveTimelineItem, ArchiveTimelineList } from "@/components/cards/ArchiveTimelineList";
import { CardBase } from "@/components/cards/CardBase";
import { buildMetricRows, HealthMetricsList } from "@/components/cards/HealthMetricsList";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider, MemberArchiveSection } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

const sectionCopy = {
  records: { title: "全部记录", heading: "健康记录", description: "查看成员已经开放的系统内记录。" },
  metrics: { title: "健康指标", heading: "健康指标", description: "查看成员已经开放的指标和历史记录。" },
  documents: { title: "医疗资料与就医历史", heading: "医疗资料与就医历史", description: "查看成员主动共享的资料和就医记录。" },
  ai: { title: "AI 整理", heading: "AI 整理", description: "仅根据成员已共享的系统内记录进行安全整理。" }
} as const;

function formatDate(value: string | null | undefined) { return value ? value.replace("T", " ").slice(0, 16) : "时间待补充"; }
function metricLabel(metricType: string) { return ({ heart_rate: "心率", sleep_duration: "睡眠", steps: "步数", temperature: "体温", weight: "体重" } as Record<string, string>)[metricType] ?? "健康指标"; }

export default function MemberArchiveSectionScreen() {
  const { id, section = "records" } = useLocalSearchParams<{ id: string; section: MemberArchiveSection }>();
  const safeSection: MemberArchiveSection = section in sectionCopy ? section : "records";
  const copy = sectionCopy[safeSection];
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const memberId = String(id ?? "me");
  const resource = useApiResource(() => provider.getMemberArchiveSection(memberId, safeSection), [memberId, safeSection, session.currentUserId, session.dataMode]);
  const data = resource.data;
  const name = data?.member.display_name ?? "家庭成员";
  const isSelf = data?.member.user_id === session.currentUserId || memberId === session.currentUserId;
  const denied = resource.errorCode === "permission_denied" || resource.errorCode === "forbidden";
  const timelineItems: ArchiveTimelineItem[] = safeSection === "records" ? [
    ...(data?.bloodPressure ?? []).map((item) => ({ date: formatDate(item.recorded_at), detail: `${item.systolic}/${item.diastolic} mmHg`, icon: "pulse-outline" as const, id: `bp-${item.id}`, title: "血压记录", tone: theme.colors.primary })),
    ...(data?.metrics ?? []).map((item) => ({ date: formatDate(item.measured_at), detail: item.value_numeric === null || item.value_numeric === undefined ? item.value_text ?? "已记录" : String(item.value_numeric), icon: "analytics-outline" as const, id: `metric-${item.id}`, title: `${metricLabel(item.metric_type)}记录`, tone: theme.colors.primary })),
    ...(data?.symptoms ?? []).map((item) => ({ date: formatDate(item.recorded_at), detail: item.summary, icon: "heart-outline" as const, id: `symptom-${item.id}`, title: item.title, tone: "#F38A69" })),
    ...(data?.documents ?? []).map((item) => ({ date: formatDate(item.created_at), detail: item.file_name, icon: "document-text-outline" as const, id: `document-${item.id}`, title: item.title, tone: "#5E9CE6" })),
    ...(data?.medicalEvents ?? []).map((item) => ({ date: formatDate(item.event_date ?? item.created_at), detail: item.hospital_or_org ?? item.event_type ?? "已保存的就医记录", icon: "medical-outline" as const, id: `event-${item.id}`, title: item.title ?? "就医记录", tone: "#E89545" }))
  ].sort((left, right) => new Date(right.date).getTime() - new Date(left.date).getTime()) : [];
  const medicalEvents = (data?.medicalEvents ?? []).map((item) => ({ date: formatDate(item.event_date ?? item.created_at), detail: item.hospital_or_org ?? item.event_type ?? "已保存的就医记录", icon: "medical-outline" as const, id: item.id, title: item.title ?? "就医记录", tone: "#E89545" }));

  return <AppScreen>
    <ArchiveSubHeader title={isSelf ? `我的${copy.title}` : `${name}的${copy.title}`} />
    {resource.loading ? <Text style={styles.loading}>正在读取成员共享资料…</Text> : null}
    {denied ? <CardBase style={styles.denied}><Text style={styles.deniedTitle}>暂无查看权限</Text><Text style={styles.deniedText}>该成员未向你开放此类健康资料，系统不会展示记录或详情。</Text></CardBase> : null}
    {resource.error && !denied ? <ApiErrorState message={resource.error} /> : null}
    {data && !denied ? <>
      {safeSection === "documents" ? <>
        <CardBase style={styles.documentHero}><View style={styles.documentIcon}><Ionicons color={theme.colors.primary} name="documents-outline" size={24} /></View><Text style={styles.heading}>医疗资料与就医历史</Text><Text style={styles.description}>查看该成员主动共享的体检报告、检查资料和就医记录。</Text></CardBase>
        <CardBase><Text style={styles.heading}>已归档资料 · {data.documents.length} 份</Text>{data.documents.length ? data.documents.map((item) => <View key={item.id} style={styles.documentRow}><View style={styles.fileIcon}><Ionicons color="#E96A5D" name={item.file_mime_type?.startsWith("image/") ? "image-outline" : "document-text-outline"} size={20} /></View><View style={styles.fileCopy}><Text numberOfLines={1} style={styles.fileTitle}>{item.title || item.file_name}</Text><Text style={styles.fileMeta}>{formatDate(item.created_at)}</Text></View><Ionicons color={theme.colors.subtle} name="chevron-forward" size={18} /></View>) : <Text style={styles.empty}>系统内暂无可展示的已共享医疗资料。</Text>}</CardBase>
        <CardBase><Text style={styles.heading}>就医历史 · {data.medicalEvents.length} 条</Text>{medicalEvents.length ? <ArchiveTimelineList items={medicalEvents} title="" /> : <Text style={styles.empty}>系统内暂无可展示的已共享就医记录。</Text>}</CardBase>
      </> : <>
        <CardBase><Text style={styles.heading}>{copy.heading}</Text><Text style={styles.description}>{copy.description}</Text>{safeSection === "ai" ? <Text style={styles.summary}>{data.profileSummary ?? "系统内暂时无可展示的已共享整理资料。"}</Text> : null}</CardBase>
        {safeSection === "metrics" ? <HealthMetricsList onPress={(metric) => router.push(routes.memberMetric(memberId, metric))} rows={buildMetricRows(data.bloodPressure, data.metrics)} /> : safeSection === "records" ? (timelineItems.length ? <ArchiveTimelineList items={timelineItems} title="历史记录" /> : <CardBase><Text style={styles.empty}>系统内暂无可展示的已共享记录。</Text></CardBase>) : <CardBase style={styles.notice}><Text style={styles.noticeText}>以上内容基于系统内已共享记录整理，不替代医生判断。</Text></CardBase>}
      </>}
    </> : null}
  </AppScreen>;
}

const styles = StyleSheet.create({
  denied: { gap: 10, paddingVertical: 28 }, deniedText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 21 }, deniedTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  description: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20, marginTop: 8 }, documentHero: { gap: 7 }, documentIcon: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 14, height: 48, justifyContent: "center", width: 48 },
  documentRow: { alignItems: "center", borderTopColor: theme.colors.line, borderTopWidth: 1, flexDirection: "row", gap: 10, marginTop: 10, paddingTop: 10 }, empty: { color: theme.colors.subtle, fontSize: 14, textAlign: "center" },
  fileCopy: { flex: 1 }, fileIcon: { alignItems: "center", backgroundColor: theme.colors.coralSoft, borderRadius: 12, height: 42, justifyContent: "center", width: 42 }, fileMeta: { color: theme.colors.subtle, fontSize: 11, marginTop: 3 }, fileTitle: { color: theme.colors.ink, fontSize: 13, fontWeight: "800" },
  heading: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" }, loading: { color: theme.colors.subtle, fontSize: 13 }, notice: { backgroundColor: theme.colors.tealSoft }, noticeText: { color: theme.colors.primaryDark, fontSize: 12, lineHeight: 19 }, summary: { color: theme.colors.ink, fontSize: 14, fontWeight: "800", lineHeight: 21, marginTop: 15 }
});
