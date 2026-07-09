import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { routes } from "@/lib/routes";

const metricCards = [
  { label: "睡眠", value: "6.8 小时", note: "最近 7 天记录", icon: "moon-outline", tone: "blue" },
  { label: "步数", value: "6,420", note: "今日演示数据", icon: "footsteps-outline", tone: "mint" },
  { label: "血压", value: "120/78", note: "最近一次记录", icon: "pulse-outline", tone: "orange" },
  { label: "体重/BMI", value: "62 kg", note: "长期档案入口", icon: "scale-outline", tone: "purple" }
] as const;

const timeline = [
  "今天：整理了一条血压记录摘要",
  "昨天：新增一条普通健康提醒",
  "5 月 14 日：保存症状草稿，等待用户确认",
  "5 月 13 日：上传体检资料并生成 OCR preview"
];

export default function ArchiveScreen() {
  return (
    <AppScreen>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>健康档案</Text>
          <Text style={styles.subtitle}>长期整理系统内记录，不替代医生判断。</Text>
        </View>
        <StatusBadge label="系统内记录" tone="mint" />
      </View>

      <CardBase>
        <SectionHeader title="核心指标" action="演示数据" />
        <View style={styles.metricGrid}>
          {metricCards.map((item) => (
            <View key={item.label} style={[styles.metricCard, styles[item.tone]]}>
              <Ionicons name={item.icon} size={22} color={colors.primaryDark} />
              <Text style={styles.metricLabel}>{item.label}</Text>
              <Text style={styles.metricValue}>{item.value}</Text>
              <Text style={styles.metricNote}>{item.note}</Text>
            </View>
          ))}
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="健康时间轴" action="最近动态" />
        {timeline.map((item) => (
          <Text key={item} style={styles.timelineItem}>
            {item}
          </Text>
        ))}
      </CardBase>

      <CardBase>
        <SectionHeader title="资料与记录入口" />
        <View style={styles.linkGrid}>
          <Link href={routes.documents} style={styles.linkCard}>
            <Ionicons name="document-text-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>文档资料</Text>
            <Text style={styles.linkNote}>查看上传资料与 OCR preview</Text>
          </Link>
          <Link href={routes.drafts} style={styles.linkCard}>
            <Ionicons name="clipboard-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>待确认草稿</Text>
            <Text style={styles.linkNote}>草稿确认入库仍按受控流程</Text>
          </Link>
          <Link href={routes.createHealthEventDraft} style={styles.linkCard}>
            <Ionicons name="calendar-number-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>健康事件</Text>
            <Text style={styles.linkNote}>整理检查、复查与重要事项</Text>
          </Link>
          <Link href={routes.createSymptomDraft} style={styles.linkCard}>
            <Ionicons name="create-outline" size={24} color={colors.primary} />
            <Text style={styles.linkTitle}>症状记录</Text>
            <Text style={styles.linkNote}>先生成待确认草稿</Text>
          </Link>
        </View>
      </CardBase>

      <CardBase>
        <SectionHeader title="后续能力预留" />
        <Text style={styles.paragraph}>趋势图、CSV/Excel 导入、长期指标对比将在后续阶段完善；当前页面先作为长期健康档案主入口。</Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  blue: { backgroundColor: colors.blue },
  header: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8
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
    borderRadius: 16,
    padding: 12,
    width: "48%"
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  metricLabel: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 8
  },
  metricNote: {
    color: colors.textMuted,
    fontSize: 11,
    marginTop: 4
  },
  metricValue: {
    color: colors.text,
    fontSize: 19,
    fontWeight: "900",
    marginTop: 3
  },
  mint: { backgroundColor: colors.mint },
  orange: { backgroundColor: colors.orange },
  paragraph: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20
  },
  purple: { backgroundColor: colors.purple },
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
