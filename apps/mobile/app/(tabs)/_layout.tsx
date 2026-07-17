import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { Platform } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { theme } from "@/constants/theme";

const tabs = [
  { name: "index", title: "我的健康", icon: "home" },
  { name: "archive", title: "档案", icon: "folder-open" },
  { name: "family", title: "家庭", icon: "people" },
  { name: "agent", title: "AI", icon: "chatbubble-ellipses" },
  { name: "settings", title: "我的", icon: "person-circle" }
] as const;

export default function TabLayout() {
  const insets = useSafeAreaInsets();
  // Android's navigator already reserves the system navigation bar. Adding its
  // inset again here creates an empty white layer above the tab icons.
  const bottomInset = Platform.OS === "ios" ? insets.bottom : 0;
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.tabInactive,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "700" },
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.line,
          height: 64 + bottomInset,
          paddingBottom: Math.max(bottomInset, 8),
          paddingTop: 8
        }
      }}
    >
      {tabs.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            tabBarIcon: ({ color, size }) => (
              <Ionicons name={tab.icon} size={size} color={color} />
            )
          }}
        />
      ))}
    </Tabs>
  );
}
