import { useEffect, useState } from "react";
import { Redirect, Stack, usePathname } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { Image, StyleSheet, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { authMode, dataMode } from "@/lib/apiConfig";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function RootLayout() {
  const pathname = usePathname();
  const auth = useAuthSession();
  const [showLaunchScreen, setShowLaunchScreen] = useState(true);
  const loginRequired = dataMode === "api" && authMode === "auth";

  useEffect(() => {
    const timer = setTimeout(() => setShowLaunchScreen(false), 1300);
    return () => clearTimeout(timer);
  }, []);

  const isAuthRoute = pathname === "/login" || pathname === "/register";

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      {showLaunchScreen ? (
        <View style={styles.launchScreen}>
          <Image source={require("@/assets/branding/launch-screen.png")} resizeMode="cover" style={styles.launchImage} />
        </View>
      ) : null}
      {!showLaunchScreen && loginRequired && !auth.session && !isAuthRoute ? <Redirect href="/login" /> : null}
      {!showLaunchScreen && loginRequired && auth.session && isAuthRoute ? <Redirect href="/" /> : null}
      {!showLaunchScreen && !(loginRequired && !auth.session && !isAuthRoute) && !(loginRequired && auth.session && isAuthRoute) ? <Stack screenOptions={{ headerShown: false }} /> : null}
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  launchImage: {
    height: "100%",
    width: "100%"
  },
  launchScreen: {
    backgroundColor: "#FFFFFF",
    flex: 1
  }
});
