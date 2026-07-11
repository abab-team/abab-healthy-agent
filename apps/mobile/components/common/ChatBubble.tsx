import { Animated, StyleSheet, Text, View } from "react-native";
import { useEffect, useRef } from "react";
import { theme } from "@/constants/theme";

export function ChatBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  const isUser = role === "user";
  const progress = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.spring(progress, { damping: 16, stiffness: 180, toValue: 1, useNativeDriver: true }).start();
  }, [progress]);
  return (
    <Animated.View style={[styles.row, isUser ? styles.userRow : styles.assistantRow, { opacity: progress, transform: [{ translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [10, 0] }) }, { scale: progress.interpolate({ inputRange: [0, 1], outputRange: [0.97, 1] }) }] }]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        {!isUser ? <Text style={styles.name}>AI 健康管家</Text> : null}
        <Text style={[styles.content, isUser ? styles.userText : null]}>{content}</Text>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  assistantBubble: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderWidth: 1 },
  assistantRow: { justifyContent: "flex-start" },
  bubble: { borderRadius: 18, maxWidth: "88%", paddingHorizontal: 13, paddingVertical: 11 },
  content: { color: theme.colors.ink, fontSize: 13, lineHeight: 20 },
  name: { color: theme.colors.primaryDark, fontSize: 11, fontWeight: "900", marginBottom: 5 },
  row: { flexDirection: "row" },
  userBubble: { backgroundColor: theme.colors.primary },
  userRow: { justifyContent: "flex-end" },
  userText: { color: "#FFFFFF" }
});
