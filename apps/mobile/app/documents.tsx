import { Link } from "expo-router";
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
import type { ApiResult, MedicalDocument } from "@/types/api";

type DocumentsProvider = {
  listDocuments: () => Promise<ApiResult<{ items: MedicalDocument[]; source: "mock" | "api"; mockSections: string[] }>>;
};

export default function DocumentsScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId) as DocumentsProvider;
  const documents = useApiResource(() => provider.listDocuments(), [session.currentUserId, session.dataMode]);
  const items = documents.data?.items ?? [];

  return (
    <AppScreen>
      <Text style={styles.title}>健康资料</Text>
      <ApiModeBadge mode={session.dataMode} />
      <CardBase>
        <SectionHeader title="资料处理闭环" />
        <Text style={styles.line}>本阶段支持上传安全元数据、处理任务、演示 OCR 预览与待确认健康事件草稿。</Text>
        <Text style={styles.line}>OCR 结果不会直接成为医疗判断、用药安排或正式健康事实。</Text>
      </CardBase>
      {documents.loading ? <Text style={styles.line}>正在读取资料列表...</Text> : null}
      {documents.error ? <ApiErrorState message={documents.error} /> : null}
      <CardBase>
        <SectionHeader title="系统内资料" action={session.dataMode === "api" ? "后端数据" : "演示数据"} />
        {items.length === 0 ? <Text style={styles.line}>系统内暂无资料。真实文件选择器将在后续移动端阶段完善。</Text> : null}
        {items.map((item: MedicalDocument) => (
          <Link key={item.id} href={routes.documentDetail(item.id)} asChild>
            <Pressable style={styles.row}>
              <View style={styles.copy}>
                <Text style={styles.name}>{item.title}</Text>
                <Text style={styles.line}>{item.file_name}</Text>
              </View>
              <StatusBadge label={item.ai_extract_status} tone="blue" />
            </Pressable>
          </Link>
        ))}
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  copy: { flex: 1 },
  line: { color: colors.textMuted, fontSize: 13, lineHeight: 20, marginTop: 4 },
  name: { color: colors.text, fontSize: 15, fontWeight: "900" },
  row: {
    alignItems: "center",
    backgroundColor: colors.surfaceSoft,
    borderRadius: 14,
    flexDirection: "row",
    gap: 10,
    marginTop: 10,
    padding: 12
  },
  title: { color: colors.text, fontSize: 24, fontWeight: "900", paddingTop: 8 }
});
