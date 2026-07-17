import { Ionicons } from "@expo/vector-icons";
import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { AppScreen } from "@/components/layout/AppScreen";
import { PrimaryButton } from "@/components/common/PrimaryButton";
import { theme } from "@/constants/theme";
import { routes } from "@/lib/routes";

export default function FamilyOnboardingScreen() {
  return <AppScreen>
    <View style={styles.hero}><View style={styles.icon}><Ionicons color={theme.colors.primaryDark} name="people-outline" size={31} /></View><Text style={styles.title}>创建或加入一个家庭</Text><Text style={styles.subtitle}>加入家庭后，家人只会看到你主动开放的健康信息。</Text></View>
    <CardBase style={styles.card}><Text style={styles.cardTitle}>创建家庭</Text><Text style={styles.copy}>设置家庭名称后会生成一个 7 天有效的邀请码，可分享给家人。</Text><Link href={routes.createFamily} asChild><View><PrimaryButton label="创建家庭" onPress={() => undefined} /></View></Link></CardBase>
    <CardBase style={styles.card}><Text style={styles.cardTitle}>输入邀请码加入</Text><Text style={styles.copy}>已有家人的邀请码？输入后即可加入，并自行选择共享范围。</Text><Link href={routes.joinFamily} asChild><View><PrimaryButton label="输入邀请码" onPress={() => undefined} /></View></Link></CardBase>
    <Text style={styles.note}>你也可以暂时不加入家庭，继续使用个人健康记录。</Text>
  </AppScreen>;
}

const styles = StyleSheet.create({ card: { gap: 10 }, cardTitle: { color: theme.colors.ink, fontSize: 17, fontWeight: "900" }, copy: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20 }, hero: { alignItems: "center", paddingTop: 28 }, icon: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 24, height: 58, justifyContent: "center", width: 58 }, note: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, textAlign: "center" }, subtitle: { color: theme.colors.subtle, fontSize: 13, lineHeight: 20, textAlign: "center" }, title: { color: theme.colors.ink, fontSize: 24, fontWeight: "900", marginTop: 14 } });
