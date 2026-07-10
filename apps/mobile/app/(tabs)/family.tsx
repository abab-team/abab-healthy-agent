import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { FamilyMemberCard } from "@/components/cards/FamilyMemberCard";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ScreenHeader } from "@/components/common/ScreenHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
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
      <ScreenHeader
        subtitle="家人健康，一起守护。"
        title="家庭"
        trailing={<StatusBadge label={`${displayMembers.length} 位成员`} tone="mint" />}
      />

      <CardBase style={styles.hero}>
        <View style={styles.heroCopy}>
          <Text style={styles.familyName}>{familyName}</Text>
          <Text style={styles.familySummary}>共同管理家庭健康记录，让每一位成员的日常记录更有条理。</Text>
          <Text style={styles.caption}>家庭成员 {displayMembers.length} 人</Text>
        </View>
        <View style={styles.homeIllustration}>
          <Ionicons color="#FFFFFF" name="home" size={37} />
        </View>
      </CardBase>

      <View style={styles.listHeader}>
        <View>
          <Text style={styles.sectionTitle}>家庭成员</Text>
          <Text style={styles.sectionCaption}>点击成员卡片，查看个人资料与其共享范围。</Text>
        </View>
        <Ionicons color={theme.colors.primaryDark} name="people-outline" size={22} />
      </View>
      {overview.loading ? <Text style={styles.hint}>正在读取家庭成员…</Text> : null}
      {overview.error ? <ApiErrorState message={overview.error} /> : null}
      <View style={styles.memberList}>
        {displayMembers.map((member, index) => (
          <FamilyMemberCard
            key={member.id}
            avatar={demoMembers[index]?.avatar ?? "👤"}
            id={member.user_id}
            name={member.display_name}
            recentRecord={overview.data?.source === "api" ? "系统内已有记录摘要" : demoMembers[index]?.recentRecord ?? "演示记录"}
            relation={member.relationship_label}
          />
        ))}
      </View>
      {!overview.loading && !overview.error && displayMembers.length === 0 ? <Text style={styles.hint}>系统内暂无家庭成员记录。</Text> : null}

      <Link href={routes.inviteMember} style={styles.inviteButton}>
        <Ionicons color={theme.colors.primaryDark} name="person-add-outline" size={21} />
        <Text style={styles.inviteText}>邀请家庭成员</Text>
      </Link>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  caption: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900", marginTop: 15 },
  familyName: { color: theme.colors.ink, fontSize: 23, fontWeight: "900" },
  familySummary: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20, marginTop: 7 },
  hero: { alignItems: "center", backgroundColor: theme.colors.tealSoft, flexDirection: "row", justifyContent: "space-between", minHeight: 150 },
  heroCopy: { flex: 1, paddingRight: 10 },
  hint: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20 },
  homeIllustration: { alignItems: "center", backgroundColor: theme.colors.primary, borderRadius: 28, height: 64, justifyContent: "center", width: 64 },
  inviteButton: { alignItems: "center", borderColor: theme.colors.primary, borderRadius: theme.radius.pill, borderWidth: 1, color: theme.colors.primaryDark, flexDirection: "row", gap: 8, justifyContent: "center", minHeight: 50, paddingHorizontal: 18 },
  inviteText: { color: theme.colors.primaryDark, fontSize: 15, fontWeight: "900" },
  listHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", marginTop: 2 },
  memberList: { gap: 10 },
  sectionCaption: { color: theme.colors.subtle, fontSize: 12, marginTop: 4 },
  sectionTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" }
});
