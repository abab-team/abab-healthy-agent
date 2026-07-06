import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { StatusBadge } from "@/components/common/StatusBadge";
import { colors } from "@/constants/colors";
import { routes } from "@/lib/routes";

export function PermissionSummaryCard() {
  return (
    <Link href={routes.permissionSettings}>
      <CardBase>
        <View style={styles.header}>
          <Ionicons name="shield-checkmark-outline" size={24} color={colors.primary} />
          <View style={styles.copy}>
            <Text style={styles.title}>共享权限概览</Text>
            <Text style={styles.description}>家庭成员之间已授权共享部分健康记录。</Text>
          </View>
          <StatusBadge label="查看详情" tone="mint" />
        </View>
        <View style={styles.stats}>
          <View style={styles.stat}>
            <Text style={styles.value}>3</Text>
            <Text style={styles.label}>成员总数</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.value}>6</Text>
            <Text style={styles.label}>共享数据类目</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.value}>已开启</Text>
            <Text style={styles.label}>共享状态</Text>
          </View>
        </View>
      </CardBase>
    </Link>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12
  },
  copy: {
    flex: 1
  },
  title: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800"
  },
  description: {
    color: colors.textMuted,
    fontSize: 13,
    marginTop: 4
  },
  stats: {
    flexDirection: "row",
    gap: 10,
    marginTop: 16
  },
  stat: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: 14,
    flex: 1,
    padding: 12
  },
  value: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "800"
  },
  label: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 4
  }
});
