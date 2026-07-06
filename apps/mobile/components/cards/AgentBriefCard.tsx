import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { colors } from "@/constants/colors";

export function AgentBriefCard() {
  return (
    <CardBase style={styles.card}>
      <View style={styles.copy}>
        <Text style={styles.title}>AI 今日简报</Text>
        <Text style={styles.description}>
          AI 基于系统记录生成今日家庭健康简报，帮你快速了解全家健康动态。
        </Text>
        <Link href="/agent-brief" style={styles.button}>
          生成今日简报
        </Link>
      </View>
      <View style={styles.bot}>
        <Ionicons name="sparkles-outline" size={34} color={colors.primaryDark} />
      </View>
    </CardBase>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: "center",
    backgroundColor: "#e9fbf7",
    flexDirection: "row",
    gap: 12
  },
  copy: {
    flex: 1,
    gap: 8
  },
  title: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "800"
  },
  description: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "800",
    overflow: "hidden",
    paddingHorizontal: 18,
    paddingVertical: 9,
    textAlign: "center"
  },
  bot: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderRadius: 24,
    height: 64,
    justifyContent: "center",
    width: 64
  }
});
