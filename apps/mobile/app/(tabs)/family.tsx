import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { FamilyHealthOverviewCard } from "@/components/cards/FamilyHealthOverviewCard";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ScreenHeader } from "@/components/common/ScreenHeader";
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
  const familiesResource = useApiResource(() => provider.listMyFamilies(), [session.currentUserId, session.dataMode]);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId, session.dataMode]);
  const familyName = overview.data?.family.name ?? "幸福一家";
  const members = overview.data?.members ?? [];
  const displayMembers = members.length ? members : demoMembers.map((member) => ({ display_name: member.name, family_id: "family-demo", id: member.id, relationship_label: member.relation, share_status: member.shareStatus, user_id: member.id }));

  if (session.dataMode === "api" && !familiesResource.loading && !familiesResource.error && familiesResource.data?.length === 0) {
    return <AppScreen><ScreenHeader subtitle="先创建家庭或输入家人的邀请码。" title="家庭健康" /><CardBase style={styles.emptyCard}><Ionicons color={theme.colors.primaryDark} name="people-outline" size={32} /><Text style={styles.emptyTitle}>你还没有加入家庭</Text><Text style={styles.hint}>加入后，家人只能看到彼此主动开放的信息。</Text><Link href={routes.familyOnboarding} style={styles.emptyLink}>创建或加入家庭</Link></CardBase></AppScreen>;
  }

  return (
    <AppScreen>
      <ScreenHeader subtitle="家人健康，一起守护。" title="家庭健康" trailing={<Ionicons color={theme.colors.primary} name="notifications-outline" size={21} />} />
      <View style={styles.currentFamilyRow}><Text style={styles.currentFamilyLabel}>当前家庭：</Text><Text style={styles.currentFamilyName}>{familyName}</Text></View>
      <View style={styles.sectionHeader}><Text style={styles.sectionTitle}>家庭成员</Text></View>
      {overview.loading ? <Text style={styles.hint}>正在读取家庭成员…</Text> : null}
      {overview.error ? <ApiErrorState message={overview.error} /> : null}
      <View style={styles.memberList}>
        {displayMembers.map((member, index) => {
          const demo = demoMembers.find((item) => item.id === member.user_id) ?? demoMembers[index];
          return <FamilyHealthOverviewCard key={member.id} avatar={demo?.avatar ?? "👤"} id={member.user_id} name={member.display_name} relation={member.relationship_label} />;
        })}
      </View>
      <Link href={routes.inviteMember} asChild><Pressable style={styles.inviteButton}><Ionicons color={theme.colors.primaryDark} name="person-add-outline" size={20} /><Text style={styles.inviteText}>邀请家庭成员</Text></Pressable></Link>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  currentFamilyLabel: { color: theme.colors.subtle, fontSize: 14 },
  currentFamilyName: { color: theme.colors.primaryDark, fontSize: 14, fontWeight: "900" },
  currentFamilyRow: { alignItems: "center", flexDirection: "row", marginTop: 2 },
  emptyCard: { alignItems: "center", backgroundColor: theme.colors.tealSoft, gap: 10, marginTop: 24 },
  emptyLink: { color: theme.colors.primaryDark, fontSize: 15, fontWeight: "900", marginTop: 4 },
  emptyTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  hint: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20 },
  inviteButton: { alignItems: "center", borderColor: theme.colors.primary, borderRadius: theme.radius.pill, borderWidth: 1, flexDirection: "row", gap: 8, justifyContent: "center", minHeight: 50, paddingHorizontal: 18, width: "100%" },
  inviteText: { color: theme.colors.primaryDark, fontSize: 15, fontWeight: "900" },
  memberList: { gap: 10 },
  sectionHeader: { marginTop: 2 },
  sectionTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" }
});
