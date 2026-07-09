import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { dataMode } from "@/lib/apiConfig";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { ArchiveTrendSeries, ArchiveTrends, ImportPreviewResult, ImportPreviewRow } from "@/types/api";

const sampleImportRows: ImportPreviewRow[] = [
  {
    measured_at: "2026-07-01T08:00:00Z",
    metric_type: "weight",
    unit: "kg",
    value_numeric: 62.5
  },
  {
    measured_at: "2026-07-02T20:00:00Z",
    metric_type: "steps",
    unit: "steps",
    value_numeric: 6400
  },
  {
    diastolic: 78,
    measured_at: "2026-07-03T07:30:00Z",
    metric_type: "blood_pressure",
    pulse: 70,
    systolic: 120
  }
];

const timeline = [
  "今天：系统内整理了长期档案趋势入口。",
  "昨天：新增普通健康提醒记录，提醒不是急救。",
  "5 月 14 日：保存症状草稿，等待用户确认。",
  "5 月 13 日：文档处理生成 OCR preview。"
];

function valueLabel(series: ArchiveTrendSeries): string {
  const lastPoint = series.points[series.points.length - 1];
  if (!lastPoint) {
    return "系统内暂无记录";
  }
  if (series.metric_type === "blood_pressure" && lastPoint.systolic && lastPoint.diastolic) {
    return `${lastPoint.systolic}/${lastPoint.diastolic}`;
  }
  const value = typeof lastPoint.value === "number" ? lastPoint.value.toLocaleString("zh-CN") : "-";
  return series.unit ? `${value} ${series.unit}` : value;
}

function barWidth(series: ArchiveTrendSeries, index: number): `${number}%` {
  const numericPoints = series.points
    .map((point) => (typeof point.value === "number" ? point.value : point.systolic))
    .filter((value): value is number => typeof value === "number");
  const max = Math.max(...numericPoints, 1);
  const value = numericPoints[index] ?? 0;
  return `${Math.max(16, Math.min(100, (value / max) * 100))}%`;
}

export default function ArchiveScreen() {
  const provider = useMemo(() => getDataProvider(), []);
  const [trends, setTrends] = useState<ArchiveTrends | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<ImportPreviewResult | null>(null);
  const [importLoading, setImportLoading] = useState<"preview" | "confirm" | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    provider.getArchiveTrends().then((result) => {
      if (!active) {
        return;
      }
      if (result.ok && result.data) {
        setTrends(result.data);
        setError(null);
      } else {
        setError(result.error?.message ?? "档案趋势加载失败。");
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [provider]);

  async function runImportPreview() {
    setImportLoading("preview");
    const result = await provider.previewHealthDataImport(sampleImportRows);
    setImportResult(result.ok && result.data ? result.data : null);
    setError(result.ok ? null : result.error?.message ?? "导入预览失败。");
    setImportLoading(null);
  }

  async function runImportConfirm() {
    setImportLoading("confirm");
    const result = await provider.confirmHealthDataImport(sampleImportRows);
    setImportResult(result.ok && result.data ? result.data : null);
    setError(result.ok ? null : result.error?.message ?? "确认导入失败。");
    setImportLoading(null);
  }

  const series = trends?.series ?? [];

  return (
    <AppScreen>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>健康档案</Text>
          <Text style={styles.subtitle}>长期整理系统内记录，不替代医生判断。</Text>
        </View>
        <StatusBadge label={dataMode === "api" ? "API 数据" : "演示数据"} tone="mint" />
      </View>

      <CardBase>
        <SectionHeader title="长期趋势" action={loading ? "加载中" : `${trends?.days ?? 90} 天`} />
        <Text style={styles.paragraph}>{trends?.disclaimer ?? "基于系统内记录整理，不替代医生判断。"}</Text>
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        <View style={styles.metricGrid}>
          {series.map((item) => (
            <View key={item.metric_type} style={styles.metricCard}>
              <View style={styles.metricHeader}>
                <Text style={styles.metricLabel}>{item.label}</Text>
                <Text style={styles.metricCount}>{item.count} 条</Text>
              </View>
              <Text style={styles.metricValue}>{valueLabel(item)}</Text>
              <Text style={styles.metricNote}>{item.summary}</Text>
              <View style={styles.sparkline}>
                {item.points.slice(-6).map((point, index) => (
                  <View key={`${item.metric_type}-${point.measured_at}`} style={styles.sparkTrack}>
                    <View style={[styles.sparkFill, { width: barWidth(item, index) }]} />
                  </View>
                ))}
              </View>
            </View>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="CSV / Excel 导入基础" action={dataMode === "api" ? "可预览 / 确认" : "演示模式"} />
        <Text style={styles.paragraph}>
          导入先做字段映射与校验预览；预览不会写入，确认后只写入通过校验的系统记录。
        </Text>
        <View style={styles.importRows}>
          {sampleImportRows.map((row) => (
            <View key={`${row.metric_type}-${row.measured_at}`} style={styles.importRow}>
              <Text style={styles.importMetric}>{row.metric_type}</Text>
              <Text style={styles.importValue}>
                {row.metric_type === "blood_pressure"
                  ? `${row.systolic}/${row.diastolic}`
                  : `${row.value_numeric} ${row.unit ?? ""}`}
              </Text>
            </View>
          ))}
        </View>
        <View style={styles.actionRow}>
          <Pressable
            accessibilityRole="button"
            disabled={importLoading !== null}
            onPress={runImportPreview}
            style={[styles.actionButton, styles.secondaryButton]}
          >
            <Text style={styles.secondaryButtonText}>{importLoading === "preview" ? "预览中" : "导入预览"}</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            disabled={importLoading !== null}
            onPress={runImportConfirm}
            style={styles.actionButton}
          >
            <Text style={styles.actionButtonText}>{importLoading === "confirm" ? "确认中" : "确认导入"}</Text>
          </Pressable>
        </View>
        {importResult ? (
          <View style={styles.importResult}>
            <Text style={styles.resultTitle}>{importResult.will_write ? "确认完成" : "预览完成"}</Text>
            <Text style={styles.resultText}>
              总行数 {importResult.total_count}，通过 {importResult.valid_count}，需处理 {importResult.invalid_count}。
            </Text>
            <Text style={styles.resultText}>
              {importResult.will_write
                ? `已创建 ${importResult.created_records_count ?? 0} 条系统记录。`
                : "本次预览没有写入任何正式健康数据。"}
            </Text>
            <Text style={styles.resultText}>{importResult.disclaimer}</Text>
          </View>
        ) : null}
      </CardBase>

      <CardBase>
        <SectionHeader title="健康时间轴" action="系统内记录" />
        {timeline.map((item) => (
          <Text key={item} style={styles.timelineItem}>
            {item}
          </Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="资料与草稿入口" />
        <View style={styles.linkGrid}>
          <Link href={routes.documents} style={styles.linkCard}>
            <Ionicons name="document-text-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>文档资料</Text>
            <Text style={styles.linkNote}>查看上传资料与 OCR preview。</Text>
          </Link>
          <Link href={routes.drafts} style={styles.linkCard}>
            <Ionicons name="clipboard-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>待确认草稿</Text>
            <Text style={styles.linkNote}>正式确认入库仍走受控流程。</Text>
          </Link>
          <Link href={routes.createHealthEventDraft} style={styles.linkCard}>
            <Ionicons name="calendar-number-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>健康事件</Text>
            <Text style={styles.linkNote}>整理检查、复查与重要健康事项。</Text>
          </Link>
          <Link href={routes.createSymptomDraft} style={styles.linkCard}>
            <Ionicons name="create-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>症状记录</Text>
            <Text style={styles.linkNote}>先生成待确认草稿。</Text>
          </Link>
        </View>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 14,
    flex: 1,
    minHeight: 44,
    justifyContent: "center",
    paddingHorizontal: 12
  },
  actionButtonText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "900"
  },
  actionRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14
  },
  errorText: {
    color: colors.warning,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8
  },
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
  },
  headerText: {
    flex: 1,
    paddingRight: 12
  },
  importMetric: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "800"
  },
  importResult: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 14,
    borderWidth: 1,
    marginTop: 14,
    padding: 12
  },
  importRow: {
    alignItems: "center",
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10
  },
  importRows: {
    marginTop: 10
  },
  importValue: {
    color: colors.textMuted,
    fontSize: 13
  },
  linkCard: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    padding: 12,
    width: "48%"
  },
  linkGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  linkNote: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4
  },
  linkTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "800",
    marginTop: 8
  },
  metricCard: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    padding: 12,
    width: "48%"
  },
  metricCount: {
    color: colors.primaryDark,
    fontSize: 12,
    fontWeight: "800"
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  metricHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  metricLabel: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: "700"
  },
  metricNote: {
    color: colors.textMuted,
    fontSize: 11,
    lineHeight: 16,
    marginTop: 6
  },
  metricValue: {
    color: colors.text,
    fontSize: 19,
    fontWeight: "900",
    marginTop: 6
  },
  paragraph: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20
  },
  resultText: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4
  },
  resultTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "900"
  },
  secondaryButton: {
    backgroundColor: colors.surfaceSoft,
    borderColor: colors.primary,
    borderWidth: 1
  },
  secondaryButtonText: {
    color: colors.primaryDark,
    fontSize: 14,
    fontWeight: "900"
  },
  sparkFill: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    height: 6
  },
  sparkline: {
    gap: 5,
    marginTop: 10
  },
  sparkTrack: {
    backgroundColor: colors.border,
    borderRadius: 999,
    height: 6,
    overflow: "hidden"
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 6
  },
  timelineItem: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    color: colors.textMuted,
    fontSize: 13,
    paddingVertical: 11
  },
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900"
  }
});
