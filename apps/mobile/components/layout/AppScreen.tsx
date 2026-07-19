import { useCallback, useRef } from "react";
import { useFocusEffect } from "@react-navigation/native";
import { PropsWithChildren, ReactNode } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { theme } from "@/constants/theme";
import { TabSwipeContainer } from "@/components/layout/TabSwipeContainer";

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
  const content = <View style={[scroll ? styles.scrollInner : styles.content, footer ? styles.contentWithFooter : null]}>{children}</View>;

  return (
    <TabSwipeContainer>
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.keyboardAvoiding}>
    <SafeAreaView edges={["top", "left", "right"]} style={styles.safeArea}>
      {scroll ? (
        <ScrollView ref={scrollRef} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {content}
        </ScrollView>
      ) : (
        content
      )}
      {footer ? <View style={styles.footer}>{footer}</View> : null}
    </SafeAreaView>
    </KeyboardAvoidingView>
    </TabSwipeContainer>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.colors.canvas
  },
  keyboardAvoiding: { flex: 1 },
  content: {
    flex: 1,
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xl,
    paddingHorizontal: theme.spacing.lg
  },
  scrollInner: {
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
