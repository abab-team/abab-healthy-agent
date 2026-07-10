import { PropsWithChildren, ReactNode } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { theme } from "@/constants/theme";

type AppScreenProps = PropsWithChildren<{
  scroll?: boolean;
  footer?: ReactNode;
}>;

export function AppScreen({ children, footer, scroll = true }: AppScreenProps) {
  const content = <View style={styles.content}>{children}</View>;

  return (
    <SafeAreaView style={styles.safeArea}>
      {scroll ? (
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {content}
        </ScrollView>
      ) : (
        content
      )}
      {footer ? <View style={styles.footer}>{footer}</View> : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.canvas
  },
  content: {
    flex: 1,
    gap: theme.spacing.lg,
    paddingBottom: 118,
    paddingHorizontal: theme.spacing.lg
  },
  footer: {
    backgroundColor: theme.colors.canvas,
    borderTopColor: theme.colors.line,
    borderTopWidth: 1,
    paddingBottom: 8,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: 9
  },
  scrollContent: {
    flexGrow: 1
  }
});
