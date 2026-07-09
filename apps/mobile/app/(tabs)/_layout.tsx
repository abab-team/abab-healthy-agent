import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { colors } from "@/constants/colors";

const tabs = [
  { name: "index", title: "首页", icon: "home" },
  { name: "archive", title: "档案", icon: "folder-open" },
  { name: "family", title: "家庭", icon: "people" },
  { name: "agent", title: "AI 管家", icon: "chatbubble-ellipses" },
  { name: "settings", title: "我的", icon: "person-circle" }
] as const;

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.tabInactive,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "700" },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 70,
          paddingBottom: 10,
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
