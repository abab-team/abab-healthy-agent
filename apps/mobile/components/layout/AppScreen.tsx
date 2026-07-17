import { useCallback, useRef } from "react";
import { useFocusEffect } from "@react-navigation/native";
import { PropsWithChildren, ReactNode } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { theme } from "@/constants/theme";

type AppScreenProps = PropsWithChildren<{
  scroll?: boolean;
  footer?: ReactNode;
}>;

export function AppScreen({ children, footer, scroll = true }: AppScreenProps) {
  const scrollRef = useRef<ScrollView>(null);
  useFocusEffect(useCallback(() => {
    if (scroll) {
      requestAnimationFrame(() => scrollRef.current?.scrollTo({ animated: false, y: 0 }));
    }
  }, [scroll]));
  const content = <View style={[styles.content, footer ? styles.contentWithFooter : null]}>{children}</View>;

  return (
    <SafeAreaView style={styles.safeArea}>
      {scroll ? (
        <ScrollView ref={scrollRef} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
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
    paddingBottom: theme.spacing.xl,
    paddingHorizontal: theme.spacing.lg
  },
  contentWithFooter: {
    paddingBottom: 0
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
