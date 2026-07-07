import { Link, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { ApiResult, DocumentExtractionResult, DocumentPipelineDetail, DocumentProcessingJob } from "@/types/api";

type DocumentProvider = {
  getDocumentPipelineDetail: (documentId: string) => Promise<ApiResult<DocumentPipelineDetail>>;
  createDocumentOcrJob: (documentId: string) => Promise<ApiResult<DocumentProcessingJob>>;
  runMockOcr: (jobId: string) => Promise<ApiResult<DocumentExtractionResult>>;
};

export default function DocumentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId) as DocumentProvider;
  const documentId = String(id ?? "mock-document-1");
  const detail = useApiResource(() => provider.getDocumentPipelineDetail(documentId), [documentId, session.currentUserId]);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const data = detail.data;
  const latestJob = data?.jobs[0];
  const latestResult = data?.extractionResults[0];

  async function createOcrJob() {
    setLoading(true);
    setActionError(null);
    const result = await provider.createDocumentOcrJob(documentId);
    setLoading(false);
    if (result.ok && result.data) {
      setActionMessage(`已创建 processing job：${shortId(result.data.id)}`);
    } else {
      setActionError(result.error?.message ?? "创建 processing job 失败");
    }
  }

  async function runMockOcr() {
    if (!latestJob) {
      setActionError("请先创建 processing job。");
      return;
    }
    setLoading(true);
    setActionError(null);
    const result = await provider.runMockOcr(latestJob.id);
    setLoading(false);
    if (result.ok && result.data) {
      setActionMessage(`mock OCR 已完成：${shortId(result.data.id)}。仅展示安全预览。`);
    } else {
      setActionError(result.error?.message ?? "mock OCR 失败");
    }
  }

  return (
    <AppScreen>
      <Text style={styles.title}>资料处理详情</Text>
      <ApiModeBadge mode={session.dataMode} />
      {detail.loading ? <Text style={styles.line}>正在读取文档处理状态...</Text> : null}
      {detail.error ? <ApiErrorState message={detail.error} /> : null}
      {actionError ? <ApiErrorState message={actionError} /> : null}
      {actionMessage ? <Text style={styles.success}>{actionMessage}</Text> : null}

      <CardBase>
        <SectionHeader title="文档安全摘要" />
        <Text style={styles.name}>{data?.document.title ?? "Mock 健康资料"}</Text>
        <Text style={styles.line}>文件名：{data?.document.file_name ?? "mock-report.pdf"}</Text>
        <Text style={styles.line}>处理状态：{data?.document.ai_extract_status ?? "not_started"}</Text>
        <Text style={styles.line}>本页不显示文件路径、原始 OCR 全文或本机路径。</Text>
      </CardBase>

      <CardBase>
        <SectionHeader title="Processing Job" action="Phase 13.B" />
        {latestJob ? (
          <View style={styles.row}>
            <Text style={styles.line}>Job：{shortId(latestJob.id)}</Text>
            <StatusBadge label={latestJob.status} tone={latestJob.status === "success" ? "mint" : "blue"} />
          </View>
        ) : (
          <Text style={styles.line}>系统内暂无 processing job。</Text>
        )}
        <Pressable style={styles.button} onPress={createOcrJob} disabled={loading || session.dataMode === "mock"}>
          <Text style={styles.buttonText}>{session.dataMode === "mock" ? "mock mode 不真实创建" : "创建 OCR job"}</Text>
        </Pressable>
      </CardBase>

      <CardBase>
        <SectionHeader title="Mock OCR 预览" action="Phase 13.C" />
        {latestResult ? (
          <>
            <Text style={styles.line}>{latestResult.ai_summary ?? "系统内已有 OCR 安全预览。"}</Text>
            <Text style={styles.line}>状态：{latestResult.status}</Text>
          </>
        ) : (
          <Text style={styles.line}>暂无 OCR 预览。默认 OCR_ENABLED=false，需要后端显式开启 mock OCR。</Text>
        )}
        <Pressable style={styles.button} onPress={runMockOcr} disabled={loading || session.dataMode === "mock"}>
          <Text style={styles.buttonText}>{loading ? "处理中..." : "运行 mock OCR"}</Text>
        </Pressable>
      </CardBase>

      <CardBase>
        <SectionHeader title="生成健康事件草稿" action="Phase 13.D" />
        <Text style={styles.line}>草稿必须通过 Agent workflow preview/confirm，不会直接生成正式健康事件。</Text>
        <Text style={styles.line}>禁止展示 raw_extracted_text、file_path、密钥、错误堆栈或数据库语句。</Text>
        <Link href={routes.createHealthEventDraft} style={styles.link}>前往创建健康事件草稿</Link>
      </CardBase>
    </AppScreen>
  );
}

function shortId(value: string): string {
  return value.length > 14 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value;
}

const styles = StyleSheet.create({
  button: { backgroundColor: colors.primary, borderRadius: 999, marginTop: 12, paddingVertical: 12 },
  buttonText: { color: "#fff", fontSize: 14, fontWeight: "900", textAlign: "center" },
  line: { color: colors.textMuted, fontSize: 13, lineHeight: 20, marginTop: 5 },
  link: { color: colors.primaryDark, fontSize: 14, fontWeight: "900", marginTop: 12 },
  name: { color: colors.text, fontSize: 16, fontWeight: "900", marginTop: 6 },
  row: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", marginTop: 8 },
  success: { backgroundColor: colors.mint, borderRadius: 12, color: colors.primaryDark, fontSize: 13, padding: 10 },
  title: { color: colors.text, fontSize: 24, fontWeight: "900", paddingTop: 8 }
});
