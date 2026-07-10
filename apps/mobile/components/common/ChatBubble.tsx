import { StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

export function ChatBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  const isUser = role === "user";
  return (
    <View style={[styles.row, isUser ? styles.userRow : styles.assistantRow]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        {!isUser ? <Text style={styles.name}>AI 健康管家</Text> : null}
        <Text style={[styles.content, isUser ? styles.userText : null]}>{content}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  assistantBubble: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderWidth: 1 },
  assistantRow: { alignItems: "flex-start" },
  bubble: { borderRadius: 18, maxWidth: "88%", paddingHorizontal: 13, paddingVertical: 11 },
  content: { color: theme.colors.ink, fontSize: 13, lineHeight: 20 },
  name: { color: theme.colors.primaryDark, fontSize: 11, fontWeight: "900", marginBottom: 5 },
  row: { flexDirection: "row" },
  userBubble: { backgroundColor: theme.colors.primary },
  userRow: { alignItems: "flex-end" },
  userText: { color: "#FFFFFF" }
});
