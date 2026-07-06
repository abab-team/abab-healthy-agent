import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/constants/colors";

type SettingsListItemProps = {
  title: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
};

export function SettingsListItem({ title, description, icon }: SettingsListItemProps) {
  return (
    <View style={styles.item}>
      <Ionicons name={icon} size={24} color={colors.primary} />
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
      <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
    </View>
  );
}

const styles = StyleSheet.create({
  item: {
    alignItems: "center",
    flexDirection: "row",
    gap: 12,
    paddingVertical: 14
  },
  copy: {
    flex: 1
  },
  title: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "700"
  },
  description: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 3
  }
});
