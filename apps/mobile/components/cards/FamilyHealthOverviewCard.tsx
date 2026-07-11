import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

type FamilyHealthOverviewCardProps = {
  id: string;
  avatar: string;
  name: string;
  relation: string;
  primary: { label: string; value: string };
  secondary: { label: string; value: string };
  restricted?: boolean;
};

export function FamilyHealthOverviewCard({ id, avatar, name, relation, primary, secondary, restricted = false }: FamilyHealthOverviewCardProps) {
  return (
    <Link href={`/member/${id}`} asChild>
      <Pressable style={styles.card}>
        <View style={styles.heading}>
          <View style={styles.person}><Text style={styles.avatar}>{avatar}</Text><View><Text style={styles.name}>{name}</Text><Text style={styles.relation}>{relation}</Text></View></View>
          <Ionicons color={theme.colors.subtle} name="chevron-forward" size={19} />
        </View>
        {restricted ? <View style={styles.restricted}><Ionicons color={theme.colors.subtle} name="lock-closed-outline" size={15} /><Text style={styles.restrictedText}>该成员暂未向你开放健康资料</Text></View> : (
          <View style={styles.metrics}>
            <View style={styles.metric}><Text style={styles.metricLabel}>{primary.label}</Text><Text style={styles.metricValue}>{primary.value}</Text></View>
            <View style={styles.divider} />
            <View style={styles.metric}><Text style={styles.metricLabel}>{secondary.label}</Text><Text style={styles.metricValue}>{secondary.value}</Text></View>
          </View>
        )}
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  avatar: { fontSize: 34 },
  card: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, gap: 13, padding: 14 },
  divider: { backgroundColor: theme.colors.line, height: 32, width: 1 },
  heading: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  metric: { flex: 1 },
  metricLabel: { color: theme.colors.subtle, fontSize: 11 },
  metricValue: { color: theme.colors.ink, fontSize: 14, fontWeight: "900", marginTop: 4 },
  metrics: { alignItems: "center", flexDirection: "row", gap: 12 },
  name: { color: theme.colors.ink, fontSize: 15, fontWeight: "900" },
  person: { alignItems: "center", flexDirection: "row", gap: 9 },
  relation: { color: theme.colors.subtle, fontSize: 11, marginTop: 2 },
  restricted: { alignItems: "center", backgroundColor: "#F4F7F6", borderRadius: 10, flexDirection: "row", gap: 7, padding: 11 },
  restrictedText: { color: theme.colors.subtle, fontSize: 12, fontWeight: "700" }
});
