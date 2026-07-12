import { Redirect, Stack, usePathname } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { authMode, dataMode } from "@/lib/apiConfig";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function RootLayout() {
  const pathname = usePathname();
  const auth = useAuthSession();
  const loginRequired = dataMode === "api" && authMode === "auth";

  if (loginRequired && !auth.session && pathname !== "/login") {
    return <Redirect href="/login" />;
  }

  if (loginRequired && auth.session && pathname === "/login") {
    return <Redirect href="/(tabs)" />;
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false }} />
    </>
  );
}
