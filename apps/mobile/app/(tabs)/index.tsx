import { Link } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { MemberHealthCard } from "@/components/cards/MemberHealthCard";
import { QuickActionGrid } from "@/components/cards/QuickActionGrid";
import { TodoItem } from "@/components/cards/TodoItem";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { MockDataBadge } from "@/components/common/MockDataBadge";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { currentUser, members as mockMembers, recentActivities, todos } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import { useState } from "react";
import type { AgentRunResponse } from "@/types/api";

function shortId(id: string): string {
  return id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-6)}` : id;
}

export default function HomeScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId]);
  const [brief, setBrief] = useState<AgentRunResponse | null>(null);
  const [briefError, setBriefError] = useState<string | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
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
        <ApiModeBadge mode={overview.data?.source ?? session.dataMode} />
        {overview.loading ? <Text style={styles.hint}>正在读取家庭概览...</Text> : null}
        {overview.error ? <ApiErrorState message={overview.error} /> : null}
        {!overview.loading && !overview.error && cardMembers.length === 0 ? (
          <Text style={styles.hint}>系统内暂无家庭成员记录。</Text>
        ) : null}
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
        <MockDataBadge />
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

      <CardBase style={styles.briefCard}>
        <SectionHeader title="AI 今日简报" action={session.dataMode === "api" ? "daily_health_brief API" : "mock"} />
        <Text style={styles.hint}>只调用受控 daily_health_brief，不接写入类 workflow。</Text>
        <Pressable
          style={styles.button}
          onPress={async () => {
            setBriefLoading(true);
            setBriefError(null);
            const result = await provider.runDailyHealthBrief(session.currentUserId);
            setBriefLoading(false);
            if (result.ok && result.data) {
              setBrief(result.data);
            } else {
              setBriefError(result.error?.message ?? "生成失败");
            }
          }}
        >
          <Text style={styles.buttonText}>{briefLoading ? "生成中..." : "生成今日简报"}</Text>
        </Pressable>
        {briefError ? <ApiErrorState message={briefError} /> : null}
        {brief ? (
          <View style={styles.briefResult}>
            <Text style={styles.hint}>Trace ID：{shortId(brief.trace_id)}</Text>
            <Text style={styles.briefText}>{brief.generated_content}</Text>
            <Link href={routes.agentRun(brief.trace_id)} style={styles.link}>查看 Agent Run 详情</Link>
          </View>
        ) : null}
      </CardBase>

      <CardBase>
        <SectionHeader title="快速记录" action="写入仍为 mock" />
        <MockDataBadge label="mock / 不真实提交" />
        <QuickActionGrid />
      </CardBase>

      <CardBase>
        <SectionHeader title="最近动态" action="mock 占位" />
        <MockDataBadge />
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
  briefCard: {
    backgroundColor: "#e9fbf7"
  },
  briefResult: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    marginTop: 12,
    padding: 12
  },
  briefText: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    marginTop: 12,
    paddingVertical: 11
  },
  buttonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "800",
    textAlign: "center"
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
  link: {
    color: colors.primaryDark,
    fontSize: 13,
    fontWeight: "800",
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
