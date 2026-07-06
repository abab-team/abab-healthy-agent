import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { DraftReviewCard } from "@/components/cards/DraftReviewCard";
import { SafetyNotice } from "@/components/common/SafetyNotice";
import { SectionHeader } from "@/components/common/SectionHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { pendingDrafts } from "@/constants/mockData";

export default function DraftsScreen() {
  return (
    <AppScreen>
      <Text style={styles.title}>待确认草稿</Text>
      <SafetyNotice text="草稿只有在你明确确认后，才会进入正式健康记录；你可以编辑或忽略。" />
      {pendingDrafts.map((draft) => (
        <DraftReviewCard key={draft.id} {...draft} />
      ))}
      <CardBase>
        <SectionHeader title="草稿操作示意" />
        <View style={styles.actions}>
          <StatusBadge label="确认入库" tone="mint" />
          <StatusBadge label="编辑草稿" tone="blue" />
          <StatusBadge label="忽略草稿" tone="orange" />
        </View>
        <Text style={styles.note}>当前页面为静态原型，不会写入任何数据。</Text>
      </CardBase>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "900",
    paddingTop: 8
  },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12
  },
  note: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 20,
    marginTop: 12
  }
});
