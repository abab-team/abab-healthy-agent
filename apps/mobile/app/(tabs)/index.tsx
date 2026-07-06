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
import { currentUser, members, recentActivities, todos } from "@/constants/mockData";
import { routes } from "@/lib/routes";

export default function HomeScreen() {
  return (
    <AppScreen>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>☀️ 早上好，{currentUser.name}</Text>
          <Text style={styles.subtitle}>愿今天的每一步，都更靠近健康的生活 🌿</Text>
        </View>
        <StatusBadge label={currentUser.familyName} tone="mint" />
      </View>

      <CardBase>
        <SectionHeader title="家庭今日概览" action="查看全部 ›" />
        <View style={styles.memberGrid}>
          {members.map((member) => (
            <MemberHealthCard
              key={member.id}
              name={member.name}
              avatar={member.avatar}
              status={member.status}
              secondaryStatus={member.id === "me" ? member.secondaryStatus : undefined}
              tone={member.cardTone as "mint" | "blue" | "orange"}
              href={routes.member(member.id)}
            />
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="今日待办" action="3 项待办" />
        {todos.map((todo) => (
          <TodoItem
            key={todo.id}
            title={todo.title}
            description={todo.description}
            action={todo.action}
            icon={todo.icon as keyof typeof Ionicons.glyphMap}
            tone={todo.tone as "mint" | "orange" | "purple"}
            href={todo.id === "todo-draft" ? routes.drafts : routes.member(todo.id === "todo-review" ? "mom" : "dad")}
          />
        ))}
      </CardBase>

      <AgentBriefCard />

      <CardBase>
        <SectionHeader title="快速记录" />
        <QuickActionGrid />
      </CardBase>

      <CardBase>
        <SectionHeader title="最近动态" action="查看全部 ›" />
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
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  greeting: {
    color: colors.text,
    fontSize: 23,
    fontWeight: "900"
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 7
  },
  memberGrid: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14
  },
  activity: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    color: colors.textMuted,
    fontSize: 13,
    paddingVertical: 12
  }
});
