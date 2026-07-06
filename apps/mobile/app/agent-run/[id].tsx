import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { TraceDebugPanel } from "@/components/cards/TraceDebugPanel";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { agentRun } from "@/constants/mockData";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";

export default function AgentRunDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId);
  const traceId = String(id ?? agentRun.id);
  const detail = useApiResource(() => provider.getAgentRun(traceId), [traceId, session.currentUserId]);

  const safeDetail = detail.data ?? {
    generated_content: agentRun.generatedContent,
    safety_checks: [],
    status: "completed" as const,
    tool_calls: [],
    trace_id: traceId,
    workflow_type: "daily_health_brief" as const
  };

  return (
    <AppScreen>
      <Text style={styles.title}>Run 详情</Text>
      <StatusBadge label={session.dataMode === "api" ? "API 安全摘要" : "Mock 安全摘要"} tone="blue" />
      {detail.loading ? <Text style={styles.line}>正在读取 run / tool calls / safety checks...</Text> : null}
      {detail.error ? <ApiErrorState message={detail.error} /> : null}
      <TraceDebugPanel run={safeDetail.trace_id} toolCalls={safeDetail.tool_calls.length} safetyChecks="已脱敏" />

      <CardBase>
        <SectionHeader title="运行状态" />
        <Text style={styles.line}>Workflow Type：{safeDetail.workflow_type}</Text>
        <Text style={styles.line}>Status：{safeDetail.status}</Text>
        <Text style={styles.generated}>{safeDetail.generated_content}</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="Tool Calls" />
        {safeDetail.tool_calls.length === 0 ? <Text style={styles.line}>系统内暂无 tool call 摘要。</Text> : null}
        {safeDetail.tool_calls.map((call) => (
          <Text key={call.id} style={styles.line}>{call.name} · {call.status} · {call.summary}</Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="Safety Checks" />
        {safeDetail.safety_checks.length === 0 ? <Text style={styles.line}>系统内暂无 safety check 摘要。</Text> : null}
        {safeDetail.safety_checks.map((check) => (
          <Text key={check.id} style={styles.line}>{check.stage} · {check.status} · {check.summary}</Text>
        ))}
      </CardBase>

      <CardBase>
        <Text style={styles.line}>
          本页只展示安全摘要，不展示敏感原文、文件路径、抽取全文、密钥、错误堆栈或数据库语句。
        </Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  generated: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10
  },
  line: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 21,
    paddingVertical: 5
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  }
});
