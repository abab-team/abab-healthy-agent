import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { SectionHeader } from "@/components/common/SectionHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { recentActivities } from "@/constants/mockData";

export default function ActivityDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const index = Number(String(id ?? "activity-1").replace("activity-", "")) - 1;
  const item = recentActivities[index] ?? recentActivities[0];

  return (
    <AppScreen>
      <Text style={styles.title}>动态详情</Text>
      <CardBase>
        <SectionHeader title="系统内记录摘要" />
        <Text style={styles.text}>{item}</Text>
        <Text style={styles.text}>当前为静态 mock 详情页，不请求后端数据。</Text>
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
  text: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 22,
    marginTop: 10
  }
});
