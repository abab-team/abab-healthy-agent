import { router, useLocalSearchParams } from "expo-router";
import { useMemo } from "react";
import { StyleSheet, Text } from "react-native";
import { ArchiveEntry, ArchiveEntryList } from "@/components/cards/ArchiveEntryList";
import { ArchiveProfileCard } from "@/components/cards/ArchiveProfileCard";
import { ArchiveRecentList } from "@/components/cards/ArchiveRecentList";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

function isPermissionDenied(status: string | undefined) {
  const value = (status ?? "").toLowerCase();
  return ["未共享", "无权限", "not_shared", "denied", "none"].some((token) => value.includes(token));
}

function formatDate(value: string | null | undefined) {
  return value ? value.replace("T", " ").slice(0, 16) : "时间待补充";
}

export default function MemberDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const memberId = String(id ?? "me");
  const detail = useApiResource(() => provider.getMemberDetail(memberId), [memberId, session.currentUserId, session.dataMode]);
  const records = useApiResource(() => provider.getMemberArchiveSection(memberId, "records"), [memberId, session.currentUserId, session.dataMode]);
  const documents = useApiResource(() => provider.getMemberArchiveSection(memberId, "documents"), [memberId, session.currentUserId, session.dataMode]);
  const member = detail.data?.member ?? records.data?.member ?? documents.data?.member;
  const isSelf = member?.user_id === session.currentUserId || memberId === session.currentUserId;
  const denied = !isSelf && isPermissionDenied(member?.share_status);
  const displayName = member?.display_name ?? "家庭成员";
  const avatarUrl = member?.avatar_url?.startsWith("http") ? member.avatar_url : member?.avatar_url ? `${session.apiBaseUrl}${member.avatar_url}` : undefined;
  const openSection = (section: "records" | "metrics" | "documents" | "ai") => router.push(routes.memberSection(memberId, section));
  const symptomCount = records.data?.symptoms.length ?? 0;
  const documentCount = documents.data?.documents.length ?? 0;
  const eventCount = documents.data?.medicalEvents.length ?? 0;
  const entries: ArchiveEntry[] = [
    { count: `${symptomCount} 条`, description: "已共享的症状与健康记录", icon: "calendar-outline", id: "records", onPress: () => openSection("records"), title: "全部记录", tone: "mint" },
    { count: "", description: "查看已开放的指标和历史记录", icon: "pulse-outline", id: "metrics", onPress: () => openSection("metrics"), title: "健康指标", tone: "purple" },
    { count: `${documentCount} 份 · ${eventCount} 次`, description: "已共享的医疗资料与就医历史", icon: "documents-outline", id: "documents", onPress: () => openSection("documents"), title: "医疗资料与就医历史", tone: "blue" },
    { count: "", description: "基于已共享资料的安全整理", icon: "sparkles-outline", id: "ai", onPress: () => openSection("ai"), title: "AI 整理", tone: "teal" }
  ];
  const recentItems = [
    ...(documents.data?.documents ?? []).map((item) => ({ date: formatDate(item.created_at), detail: item.title || item.file_name, icon: "document-text-outline" as const, id: item.id, title: "医疗资料", tone: "#5E9CE6" })),
    ...(documents.data?.medicalEvents ?? []).map((item) => ({ date: formatDate(item.event_date ?? item.created_at), detail: item.hospital_or_org ?? item.event_type ?? "已保存的就医记录", icon: "medical-outline" as const, id: item.id, title: item.title ?? "就医记录", tone: "#E89545" }))
  ].sort((left, right) => new Date(right.date).getTime() - new Date(left.date).getTime()).slice(0, 3);

  return <AppScreen>
    <ArchiveSubHeader title={isSelf ? "我的健康档案" : `${displayName}的健康档案`} />
    <ArchiveProfileCard
      actionLabel={isSelf ? "管理共享权限" : "查看共享权限"}
      avatarUrl={avatarUrl}
      details={member?.relationship_label ? [["家庭关系", member.relationship_label]] : []}
      name={displayName}
      onAction={isSelf ? () => router.push(routes.permissionSettings) : undefined}
      readOnly={!isSelf}
      summary={denied ? undefined : detail.data?.profile?.summary}
    />
    {detail.loading ? <Text style={styles.loading}>正在读取家庭资料…</Text> : null}
    {detail.error ? <ApiErrorState message={detail.error} /> : null}
    {denied ? <CardBase style={styles.deniedCard}><Text style={styles.deniedTitle}>暂未查看权限</Text><Text style={styles.deniedText}>该成员尚未向你开放相关健康资料，因此这里不会展示记录或文件。</Text></CardBase> : <>
      <ArchiveEntryList entries={entries} />
      {documents.error || records.error ? <ApiErrorState message={documents.error ?? records.error ?? "资料加载失败"} /> : null}
      <ArchiveRecentList items={recentItems} onViewAll={() => openSection("documents")} title="最近归档" />
      <CardBase style={styles.noticeCard}><Text style={styles.noticeText}>仅展示成员主动开放的系统内资料；数据会随其档案记录更新。</Text></CardBase>
    </>}
  </AppScreen>;
}

const styles = StyleSheet.create({
  deniedCard: { gap: 10, paddingVertical: 28 }, deniedText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 21 }, deniedTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  loading: { color: theme.colors.subtle, fontSize: 13 }, noticeCard: { backgroundColor: theme.colors.tealSoft }, noticeText: { color: theme.colors.primaryDark, fontSize: 12, lineHeight: 19 }
});
