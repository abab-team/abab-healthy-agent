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

function isPrivateShare(status: string | undefined) {
  const value = (status ?? "").toLowerCase();
  return ["未共享", "无权限", "not_shared", "denied", "none"].some((token) => value.includes(token));
}

export default function FamilyScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const familiesResource = useApiResource(() => provider.listMyFamilies(), [session.currentUserId, session.dataMode]);
  const overview = useApiResource(() => provider.getFamilyOverview(), [session.currentUserId, session.dataMode]);
  const familyName = overview.data?.family.name ?? "幸福一家";
  const members = overview.data?.members ?? [];
  const displayMembers = members.length ? members : demoMembers.map((member) => ({ display_name: member.name, family_id: "family-demo", id: member.id, relationship_label: member.relation, share_status: member.shareStatus, user_id: member.id }));
  const isMock = overview.data?.source !== "api";
  const activities = isMock ? ["爸爸 · 记录了血压", "妈妈 · 上传了体检报告", "我 · 记录了睡眠 7.2 小时"] : [];

  if (session.dataMode === "api" && !familiesResource.loading && !familiesResource.error && familiesResource.data?.length === 0) {
    return <AppScreen><ScreenHeader subtitle="先创建家庭或输入家人的邀请码。" title="家庭健康" /><CardBase style={styles.emptyCard}><Ionicons color={theme.colors.primaryDark} name="people-outline" size={32} /><Text style={styles.emptyTitle}>你还没有加入家庭</Text><Text style={styles.hint}>加入后，家人只能看到彼此主动开放的信息。</Text><Link href={routes.familyOnboarding} style={styles.emptyLink}>创建或加入家庭</Link></CardBase></AppScreen>;
  }

  return (
    <AppScreen>
      <ScreenHeader subtitle="家人健康，一起守护。" title="家庭健康" trailing={<Ionicons color={theme.colors.primary} name="notifications-outline" size={21} />} />
      <CardBase style={styles.hero}>
        <View style={styles.heroTop}><View><Text style={styles.familyName}>{familyName}</Text><Text style={styles.familyText}>家人的健康，就像我们现在做的事</Text></View><Text style={styles.count}>{displayMembers.length} 位成员</Text></View>
        <View style={styles.avatars}>{displayMembers.slice(0, 4).map((member, index) => <View key={member.id} style={[styles.avatar, { marginLeft: index ? -8 : 0 }]}><Text>{demoMembers.find((item) => item.id === member.user_id)?.avatar ?? "👤"}</Text></View>)}</View>
        <Text style={styles.recentTitle}>最近动态</Text>
        {(isMock ? activities : ["系统内暂无可展示的家庭共享动态"]).map((activity, index) => <Text key={`${activity}-${index}`} style={styles.recentLine}>• {activity}</Text>)}
      </CardBase>
      <View style={styles.sectionHeader}><Text style={styles.sectionTitle}>家庭成员健康概览</Text><Text style={styles.action}>查看全部</Text></View>
      {overview.loading ? <Text style={styles.hint}>正在读取家庭成员…</Text> : null}
      {overview.error ? <ApiErrorState message={overview.error} /> : null}
      <View style={styles.memberList}>
        {displayMembers.map((member, index) => {
          const demo = demoMembers.find((item) => item.id === member.user_id) ?? demoMembers[index];
          const restricted = !isMock && member.user_id !== session.currentUserId && isPrivateShare(member.share_status);
          const isSelf = member.user_id === session.currentUserId;
          return <FamilyHealthOverviewCard key={member.id} avatar={demo?.avatar ?? "👤"} id={member.user_id} name={member.display_name} primary={isMock ? (isSelf ? { label: "睡眠", value: "7.2 小时" } : { label: "血压", value: index === 1 ? "120/78 mmHg" : "体检资料" }) : { label: "共享状态", value: restricted ? "未开放" : "已共享" }} relation={member.relationship_label} restricted={restricted} secondary={isMock ? (isSelf ? { label: "步数", value: "6,100 步" } : { label: "最近事件", value: index === 1 ? "内科复查" : "年度体检" }) : { label: "查看详情", value: "按权限展示" }} />;
        })}
      </View>
      <Link href={routes.inviteMember} asChild><Pressable style={styles.inviteButton}><Ionicons color={theme.colors.primaryDark} name="person-add-outline" size={20} /><Text style={styles.inviteText}>邀请家庭成员</Text></Pressable></Link>
      <View style={styles.sectionHeader}><Text style={styles.sectionTitle}>家庭健康动态</Text><Text style={styles.action}>查看全部</Text></View>
      <CardBase style={styles.activityCard}>{activities.length ? activities.map((activity, index) => <Text key={activity} style={styles.activity}>● 07-{String(10 - index).padStart(2, "0")} · {activity}</Text>) : <Text style={styles.hint}>系统内暂无可展示的家庭共享动态。</Text>}</CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  action: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  activity: { color: theme.colors.subtle, fontSize: 12, lineHeight: 23 },
  activityCard: { gap: 3 },
  avatar: { alignItems: "center", backgroundColor: "#FFFFFF", borderColor: "#D4EEE5", borderRadius: 20, borderWidth: 2, height: 40, justifyContent: "center", width: 40 },
  avatars: { flexDirection: "row", marginTop: 13 },
  count: { backgroundColor: "#D9F7EB", borderRadius: theme.radius.pill, color: theme.colors.primaryDark, fontSize: 11, fontWeight: "900", overflow: "hidden", paddingHorizontal: 8, paddingVertical: 5 },
  emptyCard: { alignItems: "center", backgroundColor: theme.colors.tealSoft, gap: 10, marginTop: 24 },
  emptyLink: { color: theme.colors.primaryDark, fontSize: 15, fontWeight: "900", marginTop: 4 },
  emptyTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "900" },
  familyName: { color: theme.colors.ink, fontSize: 20, fontWeight: "900" },
  familyText: { color: theme.colors.subtle, fontSize: 12, marginTop: 5 },
  hero: { backgroundColor: "#E5F8F1" },
  heroTop: { alignItems: "flex-start", flexDirection: "row", justifyContent: "space-between" },
  hint: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20 },
  inviteButton: { alignItems: "center", borderColor: theme.colors.primary, borderRadius: theme.radius.pill, borderWidth: 1, flexDirection: "row", gap: 8, justifyContent: "center", minHeight: 50, paddingHorizontal: 18, width: "100%" },
  inviteText: { color: theme.colors.primaryDark, fontSize: 15, fontWeight: "900" },
  memberList: { gap: 10 },
  recentLine: { color: theme.colors.subtle, fontSize: 11, lineHeight: 19 },
  recentTitle: { color: theme.colors.ink, fontSize: 12, fontWeight: "900", marginTop: 14 },
  sectionHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", marginTop: 2 },
  sectionTitle: { color: theme.colors.ink, fontSize: theme.type.section, fontWeight: "900" }
});
