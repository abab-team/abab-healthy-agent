import { Pressable, StyleSheet, Text } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ApiModeBadge } from "@/components/common/ApiModeBadge";
import { colors } from "@/constants/colors";
import type { AuthMode, DataMode, HealthStatus } from "@/types/api";

type BackendStatusCardProps = {
  apiBaseUrl: string;
  authMode: AuthMode;
  accessTokenPreview?: string;
  currentUserId: string;
  mode: DataMode;
  health?: HealthStatus | null;
  healthError?: string | null;
  loading?: boolean;
  warnings?: string[];
  onRefresh: () => void;
};

export function BackendStatusCard({
  apiBaseUrl,
  accessTokenPreview,
  authMode,
  currentUserId,
  health,
  healthError,
  loading,
  mode,
  onRefresh,
  warnings = []
}: BackendStatusCardProps) {
  return (
    <CardBase>
      <Text style={styles.title}>开发者调试</Text>
      <ApiModeBadge mode={mode} />
      <Text style={styles.line}>Auth Mode：{authMode === "auth" ? "Authorization Bearer" : "Demo Header"}</Text>
      <Text style={styles.line}>API Base URL：{apiBaseUrl || "未配置，api mode 将显示错误"}</Text>
      <Text style={styles.line}>
        {authMode === "auth" ? "当前用户 ID" : "X-Current-User-Id"}：{currentUserId || "未配置"}
      </Text>
      {authMode === "auth" ? <Text style={styles.line}>Access Token：{accessTokenPreview ?? "未登录"}</Text> : null}
      <Text style={styles.line}>
        /health：{loading ? "检查中" : healthError ? "失败" : `${health?.status ?? "mock"} · ${health?.service ?? "family-health-agent"}`}
      </Text>
      {warnings.map((warning) => (
        <Text key={warning} style={styles.warning}>{warning}</Text>
      ))}
      {healthError ? <ApiErrorState message={healthError} /> : null}
      <Text style={styles.hint}>Web 可使用 localhost；Expo Go 真机需要电脑局域网 IP，且手机和电脑在同一网络。</Text>
      <Text style={styles.hint}>api-auth mode 使用 Bearer token；api-demo mode 使用 X-Current-User-Id。</Text>
      <Pressable style={styles.button} onPress={onRefresh}>
        <Text style={styles.buttonText}>刷新 /health</Text>
      </Pressable>
    </CardBase>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.primary,
    borderRadius: 999,
    marginTop: 10,
    paddingVertical: 10
  },
  buttonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "800",
    textAlign: "center"
  },
  hint: {
    color: colors.textMuted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 6
  },
  line: {
    color: colors.textMuted,
    fontSize: 14,
    paddingVertical: 5
  },
  title: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "900",
    marginBottom: 8
  },
  warning: {
    color: colors.warning,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4
  }
});
