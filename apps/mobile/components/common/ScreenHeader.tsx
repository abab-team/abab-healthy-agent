import { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";
import { theme } from "@/constants/theme";

type ScreenHeaderProps = {
  title: string;
  subtitle?: string;
  trailing?: ReactNode;
};

export function ScreenHeader({ title, subtitle, trailing }: ScreenHeaderProps) {
  return (
    <View style={styles.row}>
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {trailing ? <View style={styles.trailing}>{trailing}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  copy: { flex: 1, paddingRight: 12 },
  row: { alignItems: "flex-start", flexDirection: "row", paddingTop: 6 },
  subtitle: { color: theme.colors.subtle, fontSize: theme.type.bodySmall, lineHeight: 19, marginTop: 6 },
  title: { color: theme.colors.ink, fontSize: theme.type.title, fontWeight: "900" },
  trailing: { marginTop: 2 }
});
