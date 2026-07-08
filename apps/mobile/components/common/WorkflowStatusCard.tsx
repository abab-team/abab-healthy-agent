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

function titleForWorkflow(workflowType: string): string {
  if (workflowType === "symptom_draft_create") {
    return "整理症状草稿";
  }
  if (workflowType === "medical_event_draft_create") {
    return "整理健康事件草稿";
  }
  if (workflowType === "alert_create") {
    return "创建健康提醒";
  }
  return "受控整理";
}

export function WorkflowStatusCard({ mode, workflowType, confirmText }: WorkflowStatusCardProps) {
  return (
    <CardBase>
      <SectionHeader title="当前操作" />
      <ApiModeBadge mode={mode} label={mode === "api" ? "已连接后端" : "演示模式"} />
      <Text style={styles.line}>
        {mode === "api"
          ? `${titleForWorkflow(workflowType)}会先预览，确认后才创建待确认草稿或普通健康提醒。`
          : "当前为演示模式，不会提交真实数据。"}
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
