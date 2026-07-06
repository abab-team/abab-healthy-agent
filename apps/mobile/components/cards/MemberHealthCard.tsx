import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { StatusBadge } from "@/components/common/StatusBadge";
import { colors } from "@/constants/colors";

type MemberHealthCardProps = {
  name: string;
  avatar: string;
  status: string;
  secondaryStatus?: string;
  tone?: "mint" | "blue" | "orange" | "purple";
};

export function MemberHealthCard({
  name,
  avatar,
  status,
  secondaryStatus,
  tone = "mint"
}: MemberHealthCardProps) {
  return (
    <CardBase style={styles.card}>
      <Text style={styles.avatar}>{avatar}</Text>
      <Text style={styles.name}>{name}</Text>
      <StatusBadge label={status} tone={tone} />
      {secondaryStatus ? <Text style={styles.note}>{secondaryStatus}</Text> : null}
    </CardBase>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: "center",
    flex: 1,
    gap: 8,
    minHeight: 132,
    paddingHorizontal: 8
  },
  avatar: {
    fontSize: 38
  },
  name: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "700"
  },
  note: {
    color: colors.warning,
    fontSize: 12,
    fontWeight: "700",
    textAlign: "center"
  }
});
