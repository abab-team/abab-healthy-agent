import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
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
      <ArchiveSubHeader title="医疗资料" />
      <ApiModeBadge mode={session.dataMode} />
      <CardBase>
        <SectionHeader title="医疗资料" action="系统内记录" />
        <Text style={styles.line}>保存体检报告、检查资料与就医文件。资料处理结果只用于日常整理，不替代医生判断。</Text>
      </CardBase>
      {documents.loading ? <Text style={styles.line}>正在读取资料列表...</Text> : null}
      {documents.error ? <ApiErrorState message={documents.error} /> : null}
      <CardBase>
        <SectionHeader title="系统内资料" action={session.dataMode === "api" ? "后端数据" : "演示数据"} />
        {items.length === 0 ? <Text style={styles.line}>系统内暂无资料。真实文件选择器将在后续移动端阶段完善。</Text> : null}
        {items.map((item: MedicalDocument) => (
          <Link key={item.id} href={routes.documentDetail(item.id)} asChild>
            <Pressable style={styles.row}>
              <View style={styles.fileIcon}><Ionicons color="#E96A5D" name="document-text-outline" size={20} /></View>
              <View style={styles.copy}>
                <Text style={styles.name}>{item.title}</Text>
                <Text style={styles.line}>{item.file_name}</Text>
              </View>
              <StatusBadge label={item.ai_extract_status} tone="blue" />
            </Pressable>
          </Link>
        ))}
      </CardBase>
      <CardBase>
        <SectionHeader title="就医历史" action="查看全部" />
        {[
          { date: "2026-06-28", label: "复查", location: "三甲医院 · 内科", title: "内科复查" },
          { date: "2026-05-20", label: "门诊", location: "三甲医院 · 神经内科", title: "普通门诊" },
          { date: "2026-04-10", label: "体检", location: "体检中心", title: "年度体检" }
        ].map((visit) => (
          <Pressable key={visit.date} onPress={() => undefined} style={styles.visitRow}>
            <View style={styles.visitIcon}><Ionicons color={colors.primary} name="medical-outline" size={18} /></View>
            <View style={styles.copy}><Text style={styles.name}>{visit.title}</Text><Text style={styles.line}>{visit.date} · {visit.location}</Text></View>
            <Text style={styles.visitTag}>{visit.label}</Text>
          </Pressable>
        ))}
      </CardBase>
      <CardBase style={styles.aiCard}>
        <View style={styles.aiHeader}><Ionicons color={colors.primaryDark} name="sparkles-outline" size={18} /><Text style={styles.aiTitle}>AI 摘要</Text><Text style={styles.aiHint}>基于你的资料生成，供参考</Text></View>
        <Text style={styles.line}>可将系统内已保存的资料整理为就医沟通摘要；不替代医生判断或治疗建议。</Text>
        <Text style={styles.aiLink}>查看完整摘要 ›</Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  copy: { flex: 1 },
  aiCard: { backgroundColor: "#ECFAF5" },
  aiHeader: { alignItems: "center", flexDirection: "row", gap: 6 },
  aiHint: { color: colors.textMuted, fontSize: 11, marginLeft: "auto" },
  aiLink: { color: colors.primaryDark, fontSize: 13, fontWeight: "800", marginTop: 12 },
  aiTitle: { color: colors.text, fontSize: 15, fontWeight: "900" },
  fileIcon: { alignItems: "center", backgroundColor: "#FFF0ED", borderRadius: 10, height: 38, justifyContent: "center", width: 38 },
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
  title: { color: colors.text, fontSize: 24, fontWeight: "900", paddingTop: 8 },
  visitIcon: { alignItems: "center", backgroundColor: "#EAF9F3", borderRadius: 10, height: 36, justifyContent: "center", width: 36 },
  visitRow: { alignItems: "center", borderTopColor: colors.border, borderTopWidth: 1, flexDirection: "row", gap: 10, paddingVertical: 12 },
  visitTag: { backgroundColor: "#EAF8FF", borderRadius: 999, color: colors.primaryDark, fontSize: 11, fontWeight: "800", overflow: "hidden", paddingHorizontal: 8, paddingVertical: 4 }
});
