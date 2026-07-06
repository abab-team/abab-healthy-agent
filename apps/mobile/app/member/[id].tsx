import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { DraftReviewCard } from "@/components/cards/DraftReviewCard";
import { PermissionSummaryCard } from "@/components/cards/PermissionSummaryCard";
import { ReminderCard } from "@/components/cards/ReminderCard";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members, pendingDrafts, reminders } from "@/constants/mockData";

export default function MemberDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const member = members.find((item) => item.id === id) ?? members[0];

  return (
    <AppScreen>
      <CardBase style={styles.hero}>
        <Text style={styles.avatar}>{member.avatar}</Text>
        <View style={styles.copy}>
          <Text style={styles.name}>{member.name}</Text>
          <StatusBadge label={member.relation} tone="mint" />
          <Text style={styles.meta}>最近记录：{member.recentRecord}</Text>
          <Text style={styles.meta}>共享：{member.shareStatus}</Text>
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="近期记录" />
        <Text style={styles.line}>根据系统内记录，最近有 3 条健康相关记录。</Text>
        <Text style={styles.line}>本页仅做记录整理，不进行健康判断。</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="今日提醒" />
        {reminders.slice(0, 1).map((reminder) => (
          <ReminderCard key={reminder.id} {...reminder} />
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="健康趋势预览" />
        <View style={styles.trendBox}>
          <Text style={styles.trendText}>血压记录 · 7 天内 4 条</Text>
          <Text style={styles.trendText}>症状记录 · 7 天内 1 条</Text>
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="待确认草稿" />
        <DraftReviewCard {...pendingDrafts[0]} />
      </CardBase>

      <PermissionSummaryCard />
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  hero: {
    alignItems: "center",
    flexDirection: "row",
    gap: 16,
    marginTop: 8
  },
  avatar: {
    fontSize: 56
  },
  copy: {
    flex: 1,
    gap: 7
  },
  name: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  },
  meta: {
    color: colors.textMuted,
    fontSize: 13
  },
  line: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
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
