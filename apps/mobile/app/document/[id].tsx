import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { getDataProvider } from "@/lib/dataProvider";
import type { ApiResult, MedicalDocument } from "@/types/api";

type DocumentProvider = {
  listDocuments: () => Promise<ApiResult<{ items: MedicalDocument[] }>>;
};

function typeLabel(value?: string | null): string {
  const labels: Record<string, string> = {
    checkup_report: "体检报告",
    lab_test: "化验单",
    medical_record: "检查资料",
    prescription: "病历 / 处方资料",
    other: "其他资料"
  };
  return value ? labels[value] ?? "医疗资料" : "医疗资料";
}

function prettySize(size?: number | null): string {
  if (!size || size < 1024) return "大小未提供";
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId) as DocumentProvider;
  const documentId = String(id ?? "mock-document-1");
  const detail = useApiResource(() => provider.listDocuments(), [documentId, session.currentUserId]);
  const document = detail.data?.items.find((item) => item.id === documentId);

  return (
    <AppScreen>
      <ArchiveSubHeader title="资料详情" />
      {detail.loading ? <Text style={styles.loading}>正在读取资料信息...</Text> : null}
      {detail.error ? <ApiErrorState message={detail.error} /> : null}
      {document ? (
        <>
          <CardBase style={styles.summaryCard}>
            <View style={styles.icon}><Ionicons color={theme.colors.primary} name={document.file_mime_type?.startsWith("image/") ? "image-outline" : "document-text-outline"} size={28} /></View>
            <Text style={styles.title}>{document.title}</Text>
            <Text style={styles.fileName}>{document.file_name}</Text>
          </CardBase>
          <CardBase>
            <DetailRow label="资料类型" value={typeLabel(document.document_type)} />
            <DetailRow label="归档日期" value={(document.document_date ?? document.created_at ?? "未提供").slice(0, 10)} />
            <DetailRow label="文件大小" value={prettySize(document.file_size)} />
            <DetailRow label="归档状态" value="已归档" />
          </CardBase>
        </>
      ) : null}
      <CardBase style={styles.notice}>
        <Ionicons color={theme.colors.primaryDark} name="shield-checkmark-outline" size={20} />
        <Text style={styles.noticeText}>资料仅用于保存与归档，当前不会自动解读内容。</Text>
      </CardBase>
    </AppScreen>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return <View style={styles.row}><Text style={styles.label}>{label}</Text><Text style={styles.value}>{value}</Text></View>;
}

const styles = StyleSheet.create({
  fileName: { color: theme.colors.subtle, fontSize: 13, marginTop: 6, textAlign: "center" },
  icon: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 16, height: 56, justifyContent: "center", width: 56 },
  label: { color: theme.colors.subtle, fontSize: 14 },
  loading: { color: theme.colors.subtle, fontSize: 13 },
  notice: { alignItems: "center", backgroundColor: theme.colors.tealSoft, flexDirection: "row", gap: 10 },
  noticeText: { color: theme.colors.primaryDark, flex: 1, fontSize: 13, fontWeight: "700", lineHeight: 19 },
  row: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", justifyContent: "space-between", paddingVertical: 14 },
  summaryCard: { alignItems: "center", paddingVertical: 24 },
  title: { color: theme.colors.ink, fontSize: 19, fontWeight: "900", marginTop: 12, textAlign: "center" },
  value: { color: theme.colors.ink, fontSize: 14, fontWeight: "800", maxWidth: "60%", textAlign: "right" }
});
