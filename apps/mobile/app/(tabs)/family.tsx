import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { FamilyMemberCard } from "@/components/cards/FamilyMemberCard";
import { PermissionSummaryCard } from "@/components/cards/PermissionSummaryCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { family, members } from "@/constants/mockData";

export default function FamilyScreen() {
  return (
    <AppScreen>
      <View style={styles.header}>
        <Text style={styles.title}>我的家庭</Text>
        <StatusBadge label="+ 邀请成员" tone="mint" />
      </View>

      <CardBase style={styles.hero}>
        <View>
          <Text style={styles.familyName}>{family.name}</Text>
          <Text style={styles.familySummary}>{family.summary}</Text>
          <Text style={styles.avatars}>{members.map((member) => member.avatar).join("  ")}  ＋</Text>
        </View>
        <Ionicons name="home-outline" size={74} color="#8dddc9" />
      </CardBase>

      {members.filter((member) => member.id !== "me").concat(members.filter((member) => member.id === "me")).map((member) => (
        <FamilyMemberCard
          key={member.id}
          id={member.id}
          avatar={member.avatar}
          name={member.name}
          relation={member.relation}
          recentRecord={member.recentRecord}
          shareStatus={member.shareStatus}
        />
      ))}

      <PermissionSummaryCard />

      <CardBase style={styles.inviteCard}>
        <Ionicons name="person-add-outline" size={26} color={colors.primary} />
        <View style={styles.inviteCopy}>
          <Text style={styles.inviteTitle}>邀请成员</Text>
          <Text style={styles.inviteText}>邀请家人加入，一起管理健康记录。</Text>
        </View>
        <StatusBadge label="去邀请" tone="mint" />
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  },
  hero: {
    alignItems: "center",
    backgroundColor: "#dff8ef",
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 150
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
  avatars: {
    fontSize: 30,
    marginTop: 18
  },
  inviteCard: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12
  },
  inviteCopy: {
    flex: 1
  },
  inviteTitle: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800"
  },
  inviteText: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 4
  }
});
