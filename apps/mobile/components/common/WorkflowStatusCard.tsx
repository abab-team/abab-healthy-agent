import { StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { ConfirmationStepCard } from "@/components/common/ConfirmationStepCard";
import { SectionHeader } from "@/components/common/SectionHeader";
import { colors } from "@/constants/colors";
import type { DataMode } from "@/types/api";

type WorkflowStatusCardProps = {
  mode: DataMode;
  workflowType: string;
  confirmText: string;
};

export function WorkflowStatusCard({ mode, workflowType, confirmText }: WorkflowStatusCardProps) {
  return (
    <CardBase>
      <SectionHeader title="当前写入状态" />
      <ApiModeBadge mode={mode} label={mode === "api" ? "API Agent workflow" : "Mock 静态预览"} />
      <Text style={styles.line}>
        {mode === "api"
          ? `将通过 POST /api/v1/agent/runs 调用固定 workflow：${workflowType}。`
          : "当前为静态预览，不会真实提交。"}
      </Text>
      <ConfirmationStepCard confirmText={confirmText} />
    </CardBase>
  );
}

const styles = StyleSheet.create({
  line: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10
  }
});
