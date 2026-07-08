import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { StatusBadge } from "@/components/common/StatusBadge";
import { colors } from "@/constants/colors";
import { routes } from "@/lib/routes";

const rows = [
  { label: "我", value: "全部共享" },
  { label: "爸爸", value: "部分共享" },
  { label: "妈妈", value: "部分共享" }
];

export function PermissionSummaryCard() {
  return (
    <Link href={routes.permissionSettings}>
      <CardBase>
        <View style={styles.header}>
          <Ionicons name="shield-checkmark-outline" size={24} color={colors.primary} />
          <View style={styles.copy}>
            <Text style={styles.title}>权限概览</Text>
            <Text style={styles.description}>家庭成员的健康记录会按共享权限展示。</Text>
          </View>
          <StatusBadge label="查看详情" tone="mint" />
        </View>
        <View style={styles.rows}>
          {rows.map((row) => (
            <View key={row.label} style={styles.row}>
              <Text style={styles.label}>{row.label}</Text>
              <Text style={styles.value}>{row.value}</Text>
            </View>
          ))}
        </View>
      </CardBase>
    </Link>
  );
}

const styles = StyleSheet.create({
  copy: {
    flex: 1
  },
  description: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 4
  },
  header: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12
  },
  label: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "800"
  },
  row: {
    alignItems: "center",
    backgroundColor: colors.surfaceSoft,
    borderRadius: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    paddingVertical: 10
  },
  rows: {
    gap: 8,
    marginTop: 14
  },
  title: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800"
  },
  value: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: "700"
  }
});
