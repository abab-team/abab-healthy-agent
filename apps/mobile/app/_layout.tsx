import { Redirect, Stack, usePathname } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { authMode, dataMode } from "@/lib/apiConfig";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function RootLayout() {
  const pathname = usePathname();
  const auth = useAuthSession();
  const loginRequired = dataMode === "api" && authMode === "auth";

  const isAuthRoute = pathname === "/login" || pathname === "/register";

  if (loginRequired && !auth.session && !isAuthRoute) {
    return <Redirect href="/login" />;
  }

  if (loginRequired && auth.session && isAuthRoute) {
    // Route groups are implementation details, not navigation targets.
    return <Redirect href="/" />;
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false }} />
    </>
  );
}
