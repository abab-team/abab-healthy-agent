import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";

type AgentActionCardProps = {
  title: string;
  description: string;
  href: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone?: "mint" | "blue" | "orange" | "purple";
};

const tones = {
  mint: colors.mint,
  blue: colors.blue,
  orange: colors.orange,
  purple: colors.purple
};

export function AgentActionCard({ title, description, href, icon, tone = "mint" }: AgentActionCardProps) {
  return (
    <Link href={href} style={[styles.card, { backgroundColor: tones[tone] }]}>
      <Ionicons name={icon} size={26} color={colors.primaryDark} />
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
    </Link>
  );
}

const styles = StyleSheet.create({
  card: {
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    flex: 1,
    minHeight: 112,
    padding: 14
  },
  copy: {
    marginTop: 10
  },
  title: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "800"
  },
  description: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4
  }
});
