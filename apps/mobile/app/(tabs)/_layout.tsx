import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
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
  const bottomInset = Math.max(insets.bottom, 8);
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
          height: 56 + bottomInset,
          paddingBottom: bottomInset,
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
