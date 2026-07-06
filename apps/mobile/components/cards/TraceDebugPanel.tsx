import { Link } from "expo-router";
import type { Href } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { colors } from "@/constants/colors";

type TraceDebugPanelProps = {
  run: string;
  toolCalls: number;
  safetyChecks: string;
  href?: Href;
};

export function TraceDebugPanel({ run, toolCalls, safetyChecks, href }: TraceDebugPanelProps) {
  const panel = (
    <CardBase style={styles.panel}>
      <View style={styles.item}>
        <Text style={styles.value}>{run}</Text>
        <Text style={styles.label}>Run</Text>
      </View>
      <View style={styles.separator} />
      <View style={styles.item}>
        <Text style={styles.value}>{toolCalls}</Text>
        <Text style={styles.label}>Tool Calls</Text>
      </View>
      <View style={styles.separator} />
      <View style={styles.item}>
        <Text style={styles.value}>{safetyChecks}</Text>
        <Text style={styles.label}>Safety Checks</Text>
      </View>
    </CardBase>
  );

  return href ? <Link href={href}>{panel}</Link> : panel;
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: "#eef6ff",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 12
  },
  item: {
    alignItems: "center",
    flex: 1
  },
  value: {
    color: colors.text,
    fontSize: 15,
    fontWeight: "800"
  },
  label: {
    color: colors.textMuted,
    fontSize: 11,
    marginTop: 3
  },
  separator: {
    backgroundColor: "#d9e7f3",
    width: 1
  }
});
