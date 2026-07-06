import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { StatusBadge } from "@/components/common/StatusBadge";
import { colors } from "@/constants/colors";
import { MemberId } from "@/constants/mockData";

type FamilyMemberCardProps = {
  id: MemberId;
  avatar: string;
  name: string;
  relation: string;
  recentRecord: string;
  shareStatus: string;
};

export function FamilyMemberCard({
  id,
  avatar,
  name,
  relation,
  recentRecord,
  shareStatus
}: FamilyMemberCardProps) {
  return (
    <CardBase style={styles.card}>
      <Text style={styles.avatar}>{avatar}</Text>
      <View style={styles.copy}>
        <View style={styles.titleRow}>
          <Text style={styles.name}>{name}</Text>
          <StatusBadge label={relation} tone="mint" />
        </View>
        <Text style={styles.meta}>最近记录：{recentRecord}</Text>
        <Text style={styles.meta}>共享：{shareStatus}</Text>
      </View>
      <Link href={`/member/${id}`}>
        <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
      </Link>
    </CardBase>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12
  },
  avatar: {
    fontSize: 38
  },
  copy: {
    flex: 1,
    gap: 5
  },
  titleRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  name: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800"
  },
  meta: {
    color: colors.textMuted,
    fontSize: 13
  }
});
