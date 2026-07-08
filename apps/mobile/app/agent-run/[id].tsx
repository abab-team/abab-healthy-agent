import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
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

function shortId(id: string): string {
  return id.length > 16 ? `${id.slice(0, 8)}...${id.slice(-6)}` : id;
}

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
      <Text style={styles.title}>执行详情</Text>
      <StatusBadge label={session.dataMode === "api" ? "后端安全摘要" : "演示安全摘要"} tone="blue" />
      {detail.loading ? <Text style={styles.line}>正在读取执行记录、步骤摘要和安全检查...</Text> : null}
      {detail.error ? <ApiErrorState message={detail.error} /> : null}
      <TraceDebugPanel run={shortId(safeDetail.trace_id)} toolCalls={safeDetail.tool_calls.length} safetyChecks="已脱敏" />

      <CardBase>
        <SectionHeader title="运行状态" />
        <View style={styles.statusGrid}>
          <View style={styles.statusBox}>
            <Text style={styles.boxLabel}>流程</Text>
            <Text style={styles.boxValue}>{safeDetail.workflow_type}</Text>
          </View>
          <View style={styles.statusBox}>
            <Text style={styles.boxLabel}>状态</Text>
            <Text style={styles.boxValue}>{safeDetail.status}</Text>
          </View>
        </View>
        <Text style={styles.line}>Trace：{shortId(safeDetail.trace_id)}</Text>
        {safeDetail.created_at ? <Text style={styles.line}>Created：{safeDetail.created_at}</Text> : null}
        {safeDetail.completed_at ? <Text style={styles.line}>Completed：{safeDetail.completed_at}</Text> : null}
        <Text style={styles.generated}>{safeDetail.generated_content}</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="步骤摘要" />
        {safeDetail.tool_calls.length === 0 ? <Text style={styles.line}>系统内暂无步骤摘要。</Text> : null}
        {safeDetail.tool_calls.map((call) => (
          <View key={call.id} style={styles.summaryRow}>
            <StatusBadge label={call.status} tone={call.status === "completed" ? "mint" : "orange"} />
            <Text style={styles.summaryText}>{call.name}</Text>
            <Text style={styles.summaryText}>{call.summary}</Text>
          </View>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="安全检查" />
        {safeDetail.safety_checks.length === 0 ? <Text style={styles.line}>系统内暂无安全检查摘要。</Text> : null}
        {safeDetail.safety_checks.map((check) => (
          <View key={check.id} style={styles.summaryRow}>
            <StatusBadge label={`${check.stage} · ${check.status}`} tone={check.status === "passed" ? "mint" : "orange"} />
            <Text style={styles.summaryText}>{check.summary}</Text>
          </View>
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
  boxLabel: {
    color: colors.textMuted,
    fontSize: 11,
    fontWeight: "800"
  },
  boxValue: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "900",
    marginTop: 4
  },
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
  statusBox: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: 12,
    flex: 1,
    padding: 10
  },
  statusGrid: {
    flexDirection: "row",
    gap: 10,
    marginTop: 10
  },
  summaryRow: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: 12,
    gap: 6,
    marginTop: 10,
    padding: 10
  },
  summaryText: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  }
});
