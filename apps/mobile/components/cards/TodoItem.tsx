import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import type { Href } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { StatusBadge } from "@/components/common/StatusBadge";
import { colors } from "@/constants/colors";

type TodoItemProps = {
  title: string;
  description: string;
  action: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone?: "mint" | "orange" | "purple" | "blue";
  href?: Href;
};

export function TodoItem({ title, description, action, icon, tone = "mint", href }: TodoItemProps) {
  const content = (
    <View style={styles.item}>
      <Ionicons name={icon} size={22} color={colors.primary} />
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
      <StatusBadge label={action} tone={tone} />
    </View>
  );

  if (!href) {
    return content;
  }

  return <Link href={href}>{content}</Link>;
}

const styles = StyleSheet.create({
  item: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    paddingVertical: 10
  },
  copy: {
    flex: 1
  },
  title: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700"
  },
  description: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 3
  }
});
