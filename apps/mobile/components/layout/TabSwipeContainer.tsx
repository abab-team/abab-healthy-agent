import { router, usePathname } from "expo-router";
import { PropsWithChildren, useMemo } from "react";
import { PanResponder, View } from "react-native";

const tabPaths = ["/", "/archive", "/family", "/agent", "/settings"] as const;
const swipeDistance = 56;

export function TabSwipeContainer({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const currentIndex = tabPaths.indexOf(pathname as (typeof tabPaths)[number]);
  const responder = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponder: (_event, gesture) => currentIndex >= 0 && Math.abs(gesture.dx) > 12 && Math.abs(gesture.dx) > Math.abs(gesture.dy),
    onPanResponderRelease: (_event, gesture) => {
      if (Math.abs(gesture.dx) < swipeDistance) return;
      const nextIndex = gesture.dx < 0 ? currentIndex + 1 : currentIndex - 1;
      if (nextIndex >= 0 && nextIndex < tabPaths.length) {
        router.navigate(tabPaths[nextIndex]);
      }
    }
  }), [currentIndex]);

  return <View {...responder.panHandlers} style={{ flex: 1 }}>{children}</View>;
}
