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
import { members as mockMembers } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

function summaryText(value: Record<string, unknown> | undefined) {
  if (!value) return "按成员的共享设置展示";
  const count = value.count ?? value.records_count ?? value.total ?? value.total_count;
  return typeof count === "number" ? `系统内 ${count} 条已共享记录` : "系统内已有已共享资料摘要";
}

function isPermissionDenied(status: string | undefined) {
  const value = (status ?? "").toLowerCase();
  return ["未共享", "无权限", "not_shared", "denied", "none"].some((token) => value.includes(token));
}

export default function MemberDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const detail = useApiResource(() => provider.getMemberDetail(String(id ?? "me")), [id, session.currentUserId, session.dataMode]);
  const mockMember = mockMembers.find((item) => item.id === id) ?? mockMembers[0];
  const member = detail.data?.member;
  const isSelf = String(id) === session.currentUserId || member?.user_id === session.currentUserId;
  const hasSharedSummary = Boolean(detail.data?.profile || detail.data?.bloodPressureSummary || detail.data?.symptomSummary || detail.data?.activeAlerts?.length);
  const denied = !isSelf && (isPermissionDenied(member?.share_status) || (detail.data?.source === "api" && !hasSharedSummary));
  const displayName = member?.display_name ?? mockMember.name;
  const openSection = (section: "records" | "metrics" | "documents" | "ai") => router.push(routes.memberSection(String(id), section));
  const archiveEntries: ArchiveEntry[] = [
    { count: "按权限", description: detail.data?.profile?.summary ?? "基础健康资料", icon: "calendar-outline", id: "records", onPress: () => openSection("records"), title: "全部记录", tone: "mint" },
    { count: "已共享", description: summaryText(detail.data?.bloodPressureSummary), icon: "pulse-outline", id: "metrics", onPress: () => openSection("metrics"), title: "健康指标", tone: "purple" },
    { count: "按权限", description: "医疗资料与就医历史", icon: "documents-outline", id: "documents", onPress: () => openSection("documents"), title: "医疗资料与就医历史", tone: "blue" },
    { count: "仅整理", description: "基于已共享资料的安全整理", icon: "sparkles-outline", id: "ai", onPress: () => openSection("ai"), title: "AI 整理", tone: "teal" }
  ];
  const recentItems = [
    { date: "最近更新", detail: summaryText(detail.data?.bloodPressureSummary), icon: "pulse-outline" as const, id: "metrics", title: "健康指标资料", tone: theme.colors.primary },
    { date: "最近更新", detail: summaryText(detail.data?.symptomSummary), icon: "heart-outline" as const, id: "symptoms", title: "健康记录资料", tone: "#F38A69" },
    { date: "资料范围", detail: "仅展示成员已开放的内容", icon: "lock-closed-outline" as const, id: "privacy", title: "共享权限", tone: "#5E9CE6" }
  ];

  return (
    <AppScreen>
      <ArchiveSubHeader title={isSelf ? "我的健康档案" : `${displayName}的健康档案`} />
      <ArchiveProfileCard
        avatar={mockMember.avatar}
        details={[["关系", member?.relationship_label ?? mockMember.relation], ["共享", member?.share_status ?? "演示中"], ["资料", denied ? "未开放" : "按权限展示"]]}
        name={displayName}
        actionLabel="管理共享权限"
        onAction={isSelf ? () => router.push(routes.permissionSettings) : undefined}
        readOnly={!isSelf}
        recentUpdate="按共享范围更新"
        summary={denied ? undefined : detail.data?.profile?.summary}
      />
      {detail.loading ? <Text style={styles.loading}>正在读取成员共享资料…</Text> : null}
      {detail.error ? <ApiErrorState message={detail.error} /> : null}
      {denied ? (
        <CardBase style={styles.deniedCard}>
          <Text style={styles.deniedTitle}>暂无查看权限</Text>
          <Text style={styles.deniedText}>该成员尚未向你开放相关健康资料。为保护隐私，此处不会展示任何健康记录、就医资料或文件详情。</Text>
        </CardBase>
      ) : (
        <>
          <ArchiveEntryList entries={archiveEntries} />
          <ArchiveRecentList items={recentItems} onViewAll={() => undefined} title="最近归档" />
          <CardBase style={styles.noticeCard}><Text style={styles.noticeText}>以上内容基于系统内已共享记录整理，不替代医生判断。</Text></CardBase>
        </>
      )}
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  deniedCard: { gap: 10, paddingVertical: 28 },
  deniedText: { color: theme.colors.subtle, fontSize: 13, lineHeight: 21 },
  deniedTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  loading: { color: theme.colors.subtle, fontSize: 13 },
  noticeCard: { backgroundColor: theme.colors.tealSoft },
  noticeText: { color: theme.colors.primaryDark, fontSize: 12, lineHeight: 19 }
});
