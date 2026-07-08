import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { FamilyMemberCard } from "@/components/cards/FamilyMemberCard";
import { PermissionSummaryCard } from "@/components/cards/PermissionSummaryCard";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { members as demoMembers } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";

export default function FamilyScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId]);
  const familyName = overview.data?.family.name ?? "幸福一家";
  const members = overview.data?.members ?? [];
  const displayMembers =
    members.length > 0
      ? members
      : demoMembers.map((member) => ({
          display_name: member.name,
          family_id: "family-demo",
          id: member.id,
          relationship_label: member.relation,
          share_status: member.shareStatus,
          user_id: member.id
        }));

  return (
    <AppScreen>
      <View style={styles.header}>
        <Text style={styles.title}>我的家庭</Text>
        <Link href={routes.inviteMember}>
          <StatusBadge label="+ 邀请成员" tone="mint" />
        </Link>
      </View>

      <CardBase style={styles.hero}>
        <View style={styles.heroCopy}>
          <Text style={styles.familyName}>{familyName}</Text>
          <Text style={styles.familySummary}>{displayMembers.length} 位成员 · 共同守护家人健康</Text>
          <ApiModeBadge mode={overview.data?.source ?? session.dataMode} />
          <Text style={styles.avatars}>{demoMembers.map((member) => member.avatar).join("  ")}  ＋</Text>
        </View>
        <Ionicons name="home-outline" size={74} color="#8dddc9" />
      </CardBase>

      {overview.loading ? <Text style={styles.hint}>正在读取家庭成员...</Text> : null}
      {overview.error ? <ApiErrorState message={overview.error} /> : null}
      {!overview.loading && !overview.error && displayMembers.length === 0 ? (
        <Text style={styles.hint}>系统内暂无家庭成员记录。</Text>
      ) : null}

      {displayMembers.map((member, index) => (
        <FamilyMemberCard
          key={member.id}
          avatar={demoMembers[index]?.avatar ?? "👤"}
          id={member.user_id}
          name={member.display_name}
          recentRecord={overview.data?.source === "api" ? "系统内记录摘要 · 后端只读接口" : demoMembers[index]?.recentRecord ?? "演示记录"}
          relation={member.relationship_label}
          shareStatus={member.share_status}
        />
      ))}

      <PermissionSummaryCard />
      <Text style={styles.hint}>
        {session.dataMode === "api" ? "成员与家庭信息来自后端；权限概览为演示摘要。" : "当前展示为演示数据。"}
      </Text>

      <Link href={routes.inviteMember}>
        <CardBase style={styles.inviteCard}>
          <Ionicons name="person-add-outline" size={26} color={colors.primary} />
          <View style={styles.inviteCopy}>
            <Text style={styles.inviteTitle}>邀请成员</Text>
            <Text style={styles.inviteText}>邀请家人加入，一起管理健康记录。</Text>
          </View>
          <StatusBadge label="去邀请" tone="mint" />
        </CardBase>
      </Link>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  avatars: {
    fontSize: 30,
    marginTop: 18
  },
  familyName: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  },
  familySummary: {
    color: colors.textMuted,
    fontSize: 14,
    marginTop: 8
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  hero: {
    alignItems: "center",
    backgroundColor: "#dff8ef",
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 150
  },
  heroCopy: {
    flex: 1
  },
  hint: {
    color: colors.textMuted,
    fontSize: 12,
    marginHorizontal: 4
  },
  inviteCard: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12
  },
  inviteCopy: {
    flex: 1
  },
  inviteText: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 4
  },
  inviteTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800"
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  }
});
