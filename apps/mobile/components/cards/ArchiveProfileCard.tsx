import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { theme } from "@/constants/theme";

type ArchiveProfileCardProps = {
  name: string;
  summary?: string;
  avatar?: string;
  details?: ReadonlyArray<readonly [string, string]>;
  recentUpdate?: string;
  readOnly?: boolean;
  actionLabel?: string;
  onAction?: () => void;
};

export function ArchiveProfileCard({
  name,
  summary,
  avatar = "👩🏻",
  details: providedDetails,
  recentUpdate,
  readOnly = false,
  actionLabel = "编辑",
  onAction
}: ArchiveProfileCardProps) {
  const profileDetails = providedDetails ?? [];
  return (
    <CardBase style={styles.card}>
      <View style={styles.heading}>
        <Text style={styles.title}>基本信息</Text>
        {readOnly ? <Text style={styles.readOnly}>共享资料</Text> : <Pressable onPress={onAction ?? (() => undefined)} style={styles.editButton}><Text style={styles.editText}>{actionLabel}</Text></Pressable>}
      </View>
      <View style={styles.body}>
        <View style={styles.avatar}><Text style={styles.avatarText}>{avatar}</Text></View>
        <View style={styles.copy}>
          <View style={styles.nameRow}>
            <Text style={styles.name}>{name}</Text>
            <Ionicons color={theme.colors.primary} name="leaf" size={17} />
          </View>
          {profileDetails.length ? <View style={styles.details}>
            {profileDetails.map(([label, value]) => (
              <View key={label} style={styles.detailRow}>
                <Text style={styles.detailLabel}>{label}</Text>
                <Text style={styles.detailValue}>{value}</Text>
              </View>
            ))}
          </View> : null}
        </View>
      </View>
      {recentUpdate ? <Text style={styles.updated}>最近更新：{recentUpdate}</Text> : null}
      {summary ? <Text numberOfLines={2} style={styles.summary}>{summary}</Text> : null}
    </CardBase>
  );
}

const styles = StyleSheet.create({
  avatar: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 24, height: 56, justifyContent: "center", width: 56 },
  avatarText: { fontSize: 33 },
  body: { alignItems: "flex-start", flexDirection: "row", gap: 14 },
  card: { backgroundColor: "#FFFFFF", paddingVertical: 14 },
  copy: { flex: 1 },
  detailLabel: { color: theme.colors.subtle, fontSize: 11, width: 40 },
  detailRow: { flexDirection: "row", gap: 8 },
  details: { gap: 4, marginTop: 7 },
  detailValue: { color: theme.colors.ink, fontSize: 12, fontWeight: "700" },
  editButton: { backgroundColor: theme.colors.tealSoft, borderRadius: theme.radius.pill, paddingHorizontal: 10, paddingVertical: 5 },
  editText: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  heading: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", marginBottom: 9 },
  name: { color: theme.colors.ink, fontSize: 19, fontWeight: "900" },
  nameRow: { alignItems: "center", flexDirection: "row", gap: 5 },
  readOnly: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "900" },
  summary: { color: theme.colors.subtle, fontSize: 11, lineHeight: 16, marginTop: 8 },
  title: { color: theme.colors.ink, fontSize: 16, fontWeight: "900" },
  updated: { color: theme.colors.primaryDark, fontSize: 11, fontWeight: "800", marginTop: 7 }
});
