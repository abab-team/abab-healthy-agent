import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useMemo } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { ArchiveEntry, ArchiveEntryList } from "@/components/cards/ArchiveEntryList";
import { ArchiveProfileCard } from "@/components/cards/ArchiveProfileCard";
import { ArchiveRecentList } from "@/components/cards/ArchiveRecentList";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { currentUser } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { ApiResult, MedicalDocument } from "@/types/api";

export default function ArchiveScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const memberDetail = useApiResource(() => provider.getMemberDetail(session.currentUserId), [session.currentUserId, session.dataMode]);
  const documents = useApiResource<{ items: MedicalDocument[] }>(
    () => provider.listDocuments() as Promise<ApiResult<{ items: MedicalDocument[] }>>,
    [session.currentUserId, session.dataMode]
  );
  const documentCount = documents.data?.items.length ?? 3;
  const name = memberDetail.data?.profile?.display_name ?? currentUser.name;

  const entries: ArchiveEntry[] = [
    { count: "1,284 条", description: "按日期查看健康记录与重要事件", icon: "calendar-outline", id: "records", onPress: () => router.push(routes.archiveRecords), title: "全部记录", tone: "mint" },
    { count: "24 类指标", description: "血压 / 睡眠 / 体重 / 步数等", icon: "pulse-outline", id: "metrics", onPress: () => router.push(routes.archiveMetrics), title: "健康指标", tone: "purple" },
    { count: `${documentCount} 份 · 18 次`, description: "体检报告、检查资料与就医历史", icon: "documents-outline", id: "documents", onPress: () => router.push(routes.documents), title: "医疗资料与就医历史", tone: "blue" },
    { count: "6 条", description: "基于系统内记录的安全整理", icon: "sparkles-outline", id: "ai", onPress: () => router.push(routes.archiveAiSummary), title: "AI 整理", tone: "teal" }
  ];

  const recentItems = [
    { date: "7 月 8 日", detail: documents.data?.items[0]?.title ?? "年度体检报告.pdf", icon: "document-text-outline" as const, id: "document", title: "新增医疗资料", tone: "#75A5F5" },
    { date: "6 月 28 日", detail: "三甲医院 · 内科", icon: "medical-outline" as const, id: "visit", title: "归档就医记录", tone: "#E89545" },
    { date: "6 月 14 日", detail: "基于系统内资料整理", icon: "sparkles-outline" as const, id: "ai-summary", title: "更新 AI 整理", tone: theme.colors.primary }
  ];

  return (
    <AppScreen>
      <ScreenHeader
        subtitle="保存你的健康记录、资料和重要事件。"
        title="健康档案"
        trailing={
          <Pressable onPress={() => undefined} style={styles.noticeButton}>
            <Ionicons color={theme.colors.ink} name="notifications-outline" size={21} />
            <View style={styles.noticeDot} />
          </Pressable>
        }
      />

      <ArchiveProfileCard name={name} summary={memberDetail.data?.profile?.summary} />
      {memberDetail.error ? <ApiErrorState message={memberDetail.error} /> : null}
      <ArchiveEntryList entries={entries} />
      {documents.error ? <ApiErrorState message={documents.error} /> : null}
      <ArchiveRecentList items={recentItems} onViewAll={() => router.push(routes.documents)} title="最近归档" />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  noticeButton: { alignItems: "center", backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.pill, borderWidth: 1, height: 40, justifyContent: "center", position: "relative", width: 40 },
  noticeDot: { backgroundColor: "#F05A5A", borderColor: "#FFFFFF", borderRadius: 5, borderWidth: 1, height: 9, position: "absolute", right: 8, top: 7, width: 9 }
});
