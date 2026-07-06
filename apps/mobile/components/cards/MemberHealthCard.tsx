import { Link } from "expo-router";
import type { Href } from "expo-router";
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
  href?: Href;
};

export function MemberHealthCard({
  name,
  avatar,
  status,
  secondaryStatus,
  tone = "mint",
  href
}: MemberHealthCardProps) {
  const card = (
    <CardBase style={styles.card}>
      <Text style={styles.avatar}>{avatar}</Text>
      <Text style={styles.name}>{name}</Text>
      <StatusBadge label={status} tone={tone} />
      {secondaryStatus ? <Text style={styles.note}>{secondaryStatus}</Text> : null}
    </CardBase>
  );

  if (!href) {
    return card;
  }

  return (
    <Link href={href} style={styles.link}>
      {card}
    </Link>
  );
}

const styles = StyleSheet.create({
  link: {
    flex: 1
  },
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
