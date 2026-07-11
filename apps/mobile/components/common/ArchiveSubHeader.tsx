import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

type ArchiveSubHeaderProps = {
  title: string;
  trailing?: "share" | "filter";
};

export function ArchiveSubHeader({ title, trailing }: ArchiveSubHeaderProps) {
  return (
    <View style={styles.row}>
      <Pressable accessibilityLabel="返回" hitSlop={10} onPress={() => router.back()} style={styles.backButton}>
        <Ionicons color={theme.colors.ink} name="chevron-back" size={25} />
      </Pressable>
      <Text numberOfLines={1} style={styles.title}>{title}</Text>
      {trailing ? (
        <Pressable accessibilityLabel={trailing === "share" ? "分享" : "筛选"} hitSlop={10} onPress={() => undefined} style={styles.trailing}>
          <Ionicons color={theme.colors.primary} name={trailing === "share" ? "share-outline" : "options-outline"} size={20} />
        </Pressable>
      ) : <View style={styles.placeholder} />}
    </View>
  );
}

const styles = StyleSheet.create({
  backButton: { alignItems: "center", height: 38, justifyContent: "center", width: 38 },
  placeholder: { width: 38 },
  row: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", paddingTop: 5 },
  title: { color: theme.colors.ink, fontSize: 19, fontWeight: "900", textAlign: "center" },
  trailing: { alignItems: "center", height: 38, justifyContent: "center", width: 38 }
});
