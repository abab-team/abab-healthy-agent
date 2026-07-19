import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

type FamilyHealthOverviewCardProps = {
  id: string;
  avatar: string;
  avatarUrl?: string | null;
  name: string;
  relation: string;
};

export function FamilyHealthOverviewCard({ id, avatar, avatarUrl, name, relation }: FamilyHealthOverviewCardProps) {
  return (
    <Link href={`/member/${id}`} asChild>
      <Pressable style={styles.card}>
        <View style={styles.heading}>
          <View style={styles.person}>{avatarUrl ? <Image source={{ uri: avatarUrl }} style={styles.avatarImage} /> : <Text style={styles.avatar}>{avatar}</Text>}<View><Text style={styles.name}>{name}</Text><Text style={styles.relation}>{relation}</Text></View></View>
          <Ionicons color={theme.colors.subtle} name="chevron-forward" size={19} />
        </View>
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  avatar: { fontSize: 38 },
  avatarImage: { borderRadius: 22, height: 44, width: 44 },
  card: { backgroundColor: "#FFFFFF", borderColor: theme.colors.line, borderRadius: theme.radius.md, borderWidth: 1, padding: 16 },
  heading: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  name: { color: theme.colors.ink, fontSize: 17, fontWeight: "900" },
  person: { alignItems: "center", flexDirection: "row", gap: 12 },
  relation: { color: theme.colors.subtle, fontSize: 11, marginTop: 2 }
});
