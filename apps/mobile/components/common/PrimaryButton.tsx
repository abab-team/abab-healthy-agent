import { Pressable, StyleSheet, Text } from "react-native";
import { theme } from "@/constants/theme";

type PrimaryButtonProps = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
};

export function PrimaryButton({ label, onPress, disabled = false }: PrimaryButtonProps) {
  return (
    <Pressable disabled={disabled} onPress={onPress} style={[styles.button, disabled ? styles.disabled : null]}>
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.pill,
    justifyContent: "center",
    minHeight: 46,
    paddingHorizontal: 18
  },
  disabled: { opacity: 0.55 },
  label: { color: "#FFFFFF", fontSize: 14, fontWeight: "900" }
});
