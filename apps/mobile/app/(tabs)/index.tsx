import { Link } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { AgentBriefCard } from "@/components/cards/AgentBriefCard";
import { CardBase } from "@/components/cards/CardBase";
import { MemberHealthCard } from "@/components/cards/MemberHealthCard";
import { QuickActionGrid } from "@/components/cards/QuickActionGrid";
import { TodoItem } from "@/components/cards/TodoItem";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { currentUser, members as mockMembers, recentActivities, todos } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

export default function HomeScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId]);
  const displayMembers = overview.data?.members ?? [];
  const cardMembers =
    displayMembers.length > 0
      ? displayMembers.map((member, index) => ({
          avatar: mockMembers[index]?.avatar ?? "👤",
          hrefId: member.user_id,
          name: member.display_name,
          status: member.share_status,
          tone: (index === 0 ? "mint" : index === 1 ? "blue" : "orange") as "mint" | "blue" | "orange"
        }))
      : mockMembers.map((member) => ({
          avatar: member.avatar,
          hrefId: member.id,
          name: member.name,
          status: member.status,
          tone: member.cardTone as "mint" | "blue" | "orange"
        }));

  return (
    <AppScreen>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>早上好，{currentUser.name}</Text>
          <Text style={styles.subtitle}>根据系统内记录，整理家庭健康事项。</Text>
        </View>
        <StatusBadge label={overview.data?.family.name ?? currentUser.familyName} tone="mint" />
      </View>

      <CardBase>
        <SectionHeader title="家庭今日概览" action={session.dataMode === "api" ? "API 只读" : "Mock"} />
        {overview.loading ? <Text style={styles.hint}>正在读取家庭概览...</Text> : null}
        {overview.error ? <Text style={styles.error}>API 暂不可用：{overview.error}</Text> : null}
        <View style={styles.memberGrid}>
          {cardMembers.map((member) => (
            <MemberHealthCard
              key={member.hrefId}
              avatar={member.avatar}
              href={routes.member(member.hrefId)}
              name={member.name}
              status={member.status}
              tone={member.tone}
            />
          ))}
        </View>
        {overview.data?.mockSections.length ? (
          <Text style={styles.hint}>以下聚合仍为 mock：{overview.data.mockSections.join("、")}</Text>
        ) : null}
      </CardBase>

      <CardBase>
        <SectionHeader title="今日待办" action="mock 占位" />
        {todos.map((todo) => (
          <TodoItem
            key={todo.id}
            action={todo.action}
            description={todo.description}
            href={todo.id === "todo-draft" ? routes.drafts : routes.member(todo.id === "todo-review" ? "mom" : "dad")}
            icon={todo.icon as keyof typeof Ionicons.glyphMap}
            title={todo.title}
            tone={todo.tone as "mint" | "orange" | "purple"}
          />
        ))}
      </CardBase>

      <AgentBriefCard />

      <CardBase>
        <SectionHeader title="快速记录" action="写入仍为 mock" />
        <QuickActionGrid />
      </CardBase>

      <CardBase>
        <SectionHeader title="最近动态" action="mock 占位" />
        {recentActivities.map((item, index) => (
          <Link key={item} href={routes.activity(`activity-${index + 1}`)}>
            <Text style={styles.activity}>{item}</Text>
          </Link>
        ))}
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  activity: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    color: colors.textMuted,
    fontSize: 13,
    paddingVertical: 12
  },
  error: {
    color: colors.warning,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 10
  },
  greeting: {
    color: colors.text,
    fontSize: 23,
    fontWeight: "900"
  },
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  hint: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 10
  },
  memberGrid: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 7
  }
});
