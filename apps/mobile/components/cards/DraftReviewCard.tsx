import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { StatusBadge } from "@/components/common/StatusBadge";
import { colors } from "@/constants/colors";

type DraftReviewCardProps = {
  type: string;
  title: string;
  createdAt: string;
  summary: string;
};

export function DraftReviewCard({ type, title, createdAt, summary }: DraftReviewCardProps) {
  return (
    <CardBase style={styles.card}>
      <View style={styles.copy}>
        <StatusBadge label={type} tone="purple" />
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.meta}>创建于 {createdAt}</Text>
        <Text style={styles.summary}>{summary}</Text>
      </View>
      <Link href="/drafts" style={styles.button}>
        去确认
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
  copy: {
    flex: 1,
    gap: 5
  },
  title: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "800"
  },
  meta: {
    color: colors.textMuted,
    fontSize: 12
  },
  summary: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18
  },
  button: {
    borderColor: "#bda8f5",
    borderRadius: 999,
    borderWidth: 1,
    color: "#6e4ad7",
    fontSize: 13,
    fontWeight: "800",
    overflow: "hidden",
    paddingHorizontal: 14,
    paddingVertical: 8
  }
});
