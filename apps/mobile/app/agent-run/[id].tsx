import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { TraceDebugPanel } from "@/components/cards/TraceDebugPanel";
import { SectionHeader } from "@/components/common/SectionHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { agentRun, safetyChecks, toolCalls } from "@/constants/mockData";

export default function AgentRunDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  return (
    <AppScreen>
      <Text style={styles.title}>Run 详情</Text>
      <TraceDebugPanel run={String(id ?? agentRun.id)} toolCalls={agentRun.toolCalls} safetyChecks={agentRun.safetyChecks} />

      <CardBase>
        <SectionHeader title="运行状态" />
        <Text style={styles.line}>Workflow Type：{agentRun.workflowType}</Text>
        <Text style={styles.line}>Status：{agentRun.status}</Text>
        <Text style={styles.generated}>{agentRun.generatedContent}</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="Tool Calls" />
        {toolCalls.map((call) => (
          <Text key={call.id} style={styles.line}>{call.name} · {call.status} · {call.summary}</Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="Safety Checks" />
        {safetyChecks.map((check) => (
          <Text key={check.id} style={styles.line}>{check.stage} · {check.status} · {check.summary}</Text>
        ))}
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  },
  line: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 21,
    paddingVertical: 5
  },
  generated: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10
  }
});
