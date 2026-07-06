import { useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { TraceDebugPanel } from "@/components/cards/TraceDebugPanel";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { agentRun } from "@/constants/mockData";
import { mockApi } from "@/lib/mockApi";
import type { AgentRunDetail } from "@/types/api";

export default function AgentRunDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [detail, setDetail] = useState<AgentRunDetail | null>(null);

  useEffect(() => {
    mockApi.getAgentRun(String(id ?? agentRun.id)).then((result) => {
      if (result.ok && result.data) {
        setDetail(result.data);
      }
    });
  }, [id]);

  const safeDetail = detail ?? {
    trace_id: String(id ?? agentRun.id),
    status: "completed" as const,
    workflow_type: "daily_health_brief" as const,
    generated_content: agentRun.generatedContent,
    tool_calls: [],
    safety_checks: []
  };

  return (
    <AppScreen>
      <Text style={styles.title}>Run 详情</Text>
      <StatusBadge label="开发调试信息" tone="blue" />
      <TraceDebugPanel run={safeDetail.trace_id} toolCalls={safeDetail.tool_calls.length} safetyChecks="已脱敏" />

      <CardBase>
        <SectionHeader title="运行状态" />
        <Text style={styles.line}>Workflow Type：{safeDetail.workflow_type}</Text>
        <Text style={styles.line}>Status：{safeDetail.status}</Text>
        <Text style={styles.generated}>{safeDetail.generated_content}</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="Tool Calls" />
        {safeDetail.tool_calls.map((call) => (
          <Text key={call.id} style={styles.line}>{call.name} · {call.status} · {call.summary}</Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="Safety Checks" />
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
