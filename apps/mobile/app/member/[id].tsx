import { Link, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { DraftReviewCard } from "@/components/cards/DraftReviewCard";
import { PermissionSummaryCard } from "@/components/cards/PermissionSummaryCard";
import { ReminderCard } from "@/components/cards/ReminderCard";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { MockDataBadge } from "@/components/common/MockDataBadge";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members as mockMembers, pendingDrafts, reminders } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

function formatSummary(value: Record<string, unknown> | undefined, fallback: string): string {
  if (!value) {
    return fallback;
  }
  const count = value.count ?? value.records_count ?? value.total ?? value.total_count;
  if (typeof count === "number") {
    return `系统内共有 ${count} 条相关记录。`;
  }
  return "系统内已有相关只读摘要。";
}

export default function MemberDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const detail = useApiResource(() => provider.getMemberDetail(String(id ?? "me")), [id, session.currentUserId]);
  const mockMember = mockMembers.find((item) => item.id === id) ?? mockMembers[0];
  const member = detail.data?.member;

  return (
    <AppScreen>
      <Link href={routes.family} style={styles.backLink}>‹ 返回家庭</Link>
      <CardBase style={styles.hero}>
        <Text style={styles.avatar}>{mockMember.avatar}</Text>
        <View style={styles.copy}>
          <Text style={styles.name}>{member?.display_name ?? mockMember.name}</Text>
          <StatusBadge label={member?.relationship_label ?? mockMember.relation} tone="mint" />
          <ApiModeBadge mode={detail.data?.source ?? session.dataMode} />
          <Text style={styles.meta}>最近记录：{mockMember.recentRecord}</Text>
          <Text style={styles.meta}>共享：{member?.share_status ?? mockMember.shareStatus}</Text>
        </View>
      </CardBase>

      {detail.loading ? <Text style={styles.line}>正在读取成员只读摘要...</Text> : null}
      {detail.error ? <ApiErrorState message={detail.error} /> : null}

      <CardBase>
        <SectionHeader title="近期记录" action={session.dataMode === "api" ? "API 只读 + mock 补位" : "mock"} />
        <Text style={styles.line}>
          {formatSummary(detail.data?.symptomSummary, "系统内暂无相关 API 摘要，当前展示 mock 占位。")}
        </Text>
        <Text style={styles.line}>本页只做记录整理，不进行健康判断。</Text>
        {detail.data?.mockSections.length ? <MockDataBadge label={`mock / 待接入：${detail.data.mockSections.join("、")}`} /> : null}
      </CardBase>

      <CardBase>
        <SectionHeader title="今日提醒" action={detail.data?.activeAlerts?.length ? "API" : "mock"} />
        {!detail.data?.activeAlerts?.length ? <MockDataBadge /> : null}
        {reminders.slice(0, 1).map((reminder) => (
          <ReminderCard key={reminder.id} {...reminder} />
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="健康趋势预览" />
        <View style={styles.trendBox}>
          <Text style={styles.trendText}>
            血压记录 · {formatSummary(detail.data?.bloodPressureSummary, "7 天内 4 条")}
          </Text>
          <Text style={styles.trendText}>症状记录 · 仅整理系统内摘要，不给健康判断</Text>
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="待确认草稿" action="mock" />
        <MockDataBadge label="mock / 不真实提交" />
        <Link href={routes.drafts}>
          <DraftReviewCard {...pendingDrafts[0]} />
        </Link>
      </CardBase>

      <PermissionSummaryCard />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  avatar: {
    fontSize: 56
  },
  backLink: {
    color: colors.primaryDark,
    fontSize: 14,
    fontWeight: "800",
    paddingTop: 8
  },
  copy: {
    flex: 1,
    gap: 7
  },
  hero: {
    alignItems: "center",
    flexDirection: "row",
    gap: 16,
    marginTop: 8
  },
  line: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
  },
  meta: {
    color: colors.textMuted,
    fontSize: 13
  },
  name: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  },
  trendBox: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: 14,
    gap: 8,
    marginTop: 10,
    padding: 14
  },
  trendText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700"
  }
});
