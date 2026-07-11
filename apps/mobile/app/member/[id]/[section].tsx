import { router, useLocalSearchParams } from "expo-router";
import { useMemo } from "react";
import { StyleSheet, Text } from "react-native";
import { ArchiveTimelineItem, ArchiveTimelineList } from "@/components/cards/ArchiveTimelineList";
import { CardBase } from "@/components/cards/CardBase";
import { buildMetricRows, HealthMetricsList } from "@/components/cards/HealthMetricsList";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { members as mockMembers } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider, MemberArchiveSection } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

const sectionCopy = {
  records: { title: "全部记录", heading: "健康记录", description: "按成员已开放的健康资料查看历史记录。" },
  metrics: { title: "健康指标", heading: "健康指标", description: "仅展示成员已开放的指标与历史记录。" },
  documents: { title: "医疗资料与就医历史", heading: "医疗资料与就医历史", description: "仅展示成员主动共享的资料和就医记录。" },
  ai: { title: "AI 整理", heading: "AI 整理", description: "只根据成员已共享的系统内记录进行安全整理。" }
} as const;

function formatDate(value: string | null | undefined) {
  return value ? value.replace("T", " ").slice(0, 16) : "最近更新";
}

export default function MemberArchiveSectionScreen() {
  const { id, section = "records" } = useLocalSearchParams<{ id: string; section: MemberArchiveSection }>();
  const safeSection: MemberArchiveSection = section in sectionCopy ? section : "records";
  const copy = sectionCopy[safeSection];
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const resource = useApiResource(() => provider.getMemberArchiveSection(String(id ?? "me"), safeSection), [id, safeSection, session.currentUserId, session.dataMode]);
  const mockMember = mockMembers.find((item) => item.id === id) ?? mockMembers[0];
  const name = resource.data?.member.display_name ?? mockMember.name;
  const isSelf = resource.data?.member.user_id === session.currentUserId || String(id) === session.currentUserId;
  const denied = resource.errorCode === "permission_denied" || resource.errorCode === "forbidden";
  const data = resource.data;
  const timelineItems: ArchiveTimelineItem[] = safeSection === "metrics" ? (data?.bloodPressure ?? []).map((item) => ({ date: formatDate(item.recorded_at), detail: `${item.systolic}/${item.diastolic} mmHg`, icon: "pulse-outline", id: item.id, title: "血压记录", tone: theme.colors.primary })) : safeSection === "records" ? (data?.symptoms ?? []).map((item) => ({ date: formatDate(item.recorded_at), detail: item.summary, icon: "heart-outline", id: item.id, title: item.title, tone: "#F38A69" })) : safeSection === "documents" ? [
    ...(data?.documents ?? []).map((item) => ({ date: formatDate(item.created_at), detail: item.file_name, icon: "document-text-outline" as const, id: item.id, title: item.title, tone: "#5E9CE6" })),
    ...(data?.medicalEvents ?? []).map((item) => ({ date: item.event_date ?? "最近更新", detail: item.hospital_or_org ?? "系统内就医记录", icon: "medical-outline" as const, id: item.id, title: item.title ?? item.event_type ?? "就医记录", tone: "#E89545" }))
  ] : [];

  return (
    <AppScreen>
      <ArchiveSubHeader title={isSelf ? `我的${copy.title}` : `${name}的${copy.title}`} />
      {resource.loading ? <Text style={styles.loading}>正在读取成员共享资料…</Text> : null}
      {denied ? <CardBase style={styles.denied}><Text style={styles.deniedTitle}>暂无查看权限</Text><Text style={styles.deniedText}>该成员未向你开放此类健康资料。为保护隐私，系统不会展示任何记录或详情。</Text></CardBase> : null}
      {resource.error && !denied ? <ApiErrorState message={resource.error} /> : null}
      {data ? <>
        <CardBase><Text style={styles.heading}>{copy.heading}</Text><Text style={styles.description}>{copy.description}</Text>{safeSection === "ai" ? <Text style={styles.summary}>{data.profileSummary ?? "系统内暂无可展示的已共享整理资料。"}</Text> : null}</CardBase>
        {safeSection === "metrics" ? <HealthMetricsList onPress={(metric) => router.push(routes.memberMetric(String(id), metric))} rows={buildMetricRows(data.bloodPressure, data.metrics)} /> : safeSection !== "ai" ? (timelineItems.length ? <ArchiveTimelineList items={timelineItems} title="历史记录" /> : <CardBase><Text style={styles.empty}>系统内暂无可展示的已共享记录。</Text></CardBase>) : <CardBase style={styles.notice}><Text style={styles.noticeText}>以上内容基于系统内已共享记录整理，不替代医生判断。</Text></CardBase>}
      </> : null}
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  denied: { gap: 10, paddingVertical: 28 },
  deniedText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 21 },
  deniedTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  description: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20, marginTop: 8 },
  empty: { color: theme.colors.subtle, fontSize: 14, textAlign: "center" },
  heading: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" },
  loading: { color: theme.colors.subtle, fontSize: 13 },
  notice: { backgroundColor: theme.colors.tealSoft },
  noticeText: { color: theme.colors.primaryDark, fontSize: 12, lineHeight: 19 },
  summary: { color: theme.colors.ink, fontSize: 14, fontWeight: "800", lineHeight: 21, marginTop: 15 }
});
