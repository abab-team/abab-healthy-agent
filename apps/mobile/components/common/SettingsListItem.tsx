import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

type SettingsListItemProps = {
  title: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
};

export function SettingsListItem({ title, description, icon }: SettingsListItemProps) {
  return (
    <View style={styles.item}>
      <View style={styles.iconWrap}>
        <Ionicons name={icon} size={20} color={theme.colors.primary} />
      </View>
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
      <Ionicons name="chevron-forward" size={18} color={theme.colors.subtle} />
    </View>
  );
}

const styles = StyleSheet.create({
  item: {
    alignItems: "center",
    borderBottomColor: theme.colors.line,
    borderBottomWidth: 1,
    flexDirection: "row",
    gap: 12,
    paddingVertical: 15
  },
  copy: {
    flex: 1
  },
  title: {
    color: theme.colors.ink,
    fontSize: 16,
    fontWeight: "800"
  },
  description: {
    color: theme.colors.subtle,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 3
  },
  iconWrap: {
    alignItems: "center",
    backgroundColor: theme.colors.tealSoft,
    borderRadius: 12,
    height: 38,
    justifyContent: "center",
    width: 38
  }
});
