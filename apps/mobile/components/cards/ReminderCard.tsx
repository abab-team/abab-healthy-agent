import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { colors } from "@/constants/colors";

type ReminderCardProps = {
  title: string;
  time: string;
  member: string;
  note: string;
};

export function ReminderCard({ title, time, member, note }: ReminderCardProps) {
  return (
    <CardBase style={styles.card}>
      <Ionicons name="alarm-outline" size={24} color={colors.warning} />
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.meta}>{member} · {time}</Text>
        <Text style={styles.note}>{note}</Text>
      </View>
    </CardBase>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: 12
  },
  copy: {
    flex: 1,
    gap: 4
  },
  title: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "800"
  },
  meta: {
    color: colors.textMuted,
    fontSize: 13
  },
  note: {
    color: colors.warning,
    fontSize: 12,
    lineHeight: 18
  }
});
