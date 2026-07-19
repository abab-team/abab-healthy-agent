import { router } from "expo-router";
import { useCallback, useMemo } from "react";
import { useFocusEffect } from "@react-navigation/native";
import { ArchiveEntry, ArchiveEntryList } from "@/components/cards/ArchiveEntryList";
import { ArchiveRecentList } from "@/components/cards/ArchiveRecentList";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { MedicalDocument } from "@/types/api";

export default function ArchiveScreen() {
  const session = useDemoSession();
  const provider = useMemo(() => getDataProvider(session.currentUserId), [session.currentUserId]);
  const recentRecords = useApiResource(() => provider.getPersonalArchiveRecentRecords(), [session.currentUserId, session.dataMode]);
  const documents = recentRecords.data?.documents ?? [];
  const medicalEvents = recentRecords.data?.medicalEvents ?? [];
  const metrics = recentRecords.data?.metrics ?? [];
  const bloodPressure = recentRecords.data?.bloodPressure ?? [];
  const symptoms = recentRecords.data?.symptoms ?? [];
  const allRecordCount = metrics.length + bloodPressure.length + symptoms.length + documents.length + medicalEvents.length;

  useFocusEffect(useCallback(() => {
    void recentRecords.reload();
  }, [recentRecords.reload]));

  const entries: ArchiveEntry[] = [
    { count: `${allRecordCount} 条`, description: "按日期查看健康记录与重要事件", icon: "calendar-outline", id: "records", onPress: () => router.push(routes.archiveRecords), title: "全部记录", tone: "mint" },
    { count: `${new Set(metrics.map((item) => item.metric_type)).size + (bloodPressure.length ? 1 : 0)} 类`, description: "血压 / 睡眠 / 体重 / 步数等", icon: "pulse-outline", id: "metrics", onPress: () => router.push(routes.archiveMetrics), title: "健康指标", tone: "purple" },
    { count: `${documents.length} 份 · ${medicalEvents.length} 次`, description: "体检报告、检查资料与就医历史", icon: "documents-outline", id: "documents", onPress: () => router.push(routes.documents), title: "医疗资料与就医历史", tone: "blue" },
    { count: "", description: "基于系统内记录的安全整理", icon: "sparkles-outline", id: "ai", onPress: () => router.push(routes.archiveAiSummary), title: "AI 整理", tone: "teal" }
  ];

  const recentItems = [
    ...documents.map((item: MedicalDocument) => ({ date: (item.document_date ?? item.created_at ?? "").replace("T", " ").slice(0, 16), detail: item.title || item.file_name, icon: "document-text-outline" as const, id: item.id, title: "新增医疗资料", tone: "#75A5F5" })),
    ...medicalEvents.map((item) => ({ date: (item.event_date ?? item.created_at ?? "").replace("T", " ").slice(0, 16), detail: item.title ?? item.event_type ?? "健康事件", icon: "medical-outline" as const, id: item.id, title: "归档健康事件", tone: "#E89545" }))
  ].filter((item) => item.date).sort((left, right) => new Date(right.date).getTime() - new Date(left.date).getTime()).slice(0, 3);

  return (
    <AppScreen>
      <ScreenHeader subtitle="保存你的健康记录、资料和重要事件。" title="健康档案" />
      <ArchiveEntryList entries={entries} />
      {recentRecords.error ? <ApiErrorState message={recentRecords.error} /> : null}
      <ArchiveRecentList items={recentItems} onViewAll={() => router.push(routes.documents)} title="最近归档" />
    </AppScreen>
  );
}
