import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { colors } from "@/constants/colors";
import { routes } from "@/lib/routes";
import type { AgentRunResponse } from "@/types/api";

type SafeResultSummaryProps = {
  title: string;
  run: AgentRunResponse;
  note: string;
};

function shortId(id: string): string {
  if (id.length <= 16) {
    return id;
  }
  return `${id.slice(0, 8)}...${id.slice(-6)}`;
}

function summaryText(run: AgentRunResponse): string {
  return run.generated_content ?? run.message ?? "系统内暂无可展示摘要。";
}

function toneForStatus(run: AgentRunResponse): "mint" | "orange" | "plain" {
  if (run.blocked || run.status === "blocked" || run.status === "failed") {
    return "orange";
  }
  if (run.status === "completed") {
    return "mint";
  }
  return "plain";
}

export function SafeResultSummary({ title, run, note }: SafeResultSummaryProps) {
  return (
    <CardBase>
      <SectionHeader title={title} />
      <View style={styles.statusRow}>
        <StatusBadge label={run.status} tone={toneForStatus(run)} />
        <Text style={styles.shortTrace}>Trace {shortId(run.trace_id)}</Text>
      </View>
      <Text style={styles.line}>Workflow：{run.workflow_type}</Text>
      <Text style={styles.generated}>{summaryText(run)}</Text>
      <Text style={styles.note}>{note}</Text>
      <Link href={routes.agentRun(run.trace_id)} style={styles.linkButton}>
        查看 Agent Run 详情
      </Link>
    </CardBase>
  );
}

const styles = StyleSheet.create({
  generated: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 8
  },
  line: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8
  },
  linkButton: {
    borderColor: colors.primary,
    borderRadius: 999,
    borderWidth: 1,
    color: colors.primaryDark,
    fontSize: 15,
    fontWeight: "800",
    marginTop: 12,
    overflow: "hidden",
    paddingVertical: 12,
    textAlign: "center"
  },
  note: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 10
  },
  shortTrace: {
    color: colors.textMuted,
    flexShrink: 1,
    fontSize: 12,
    fontWeight: "800"
  },
  statusRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 8
  }
});
