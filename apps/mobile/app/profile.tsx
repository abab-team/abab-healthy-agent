import { Ionicons } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";
import { useEffect, useState } from "react";
import { Alert, Image, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AppScreen } from "@/components/layout/AppScreen";
import { theme } from "@/constants/theme";
import { useDemoSession } from "@/hooks/useDemoSession";
import { backendApi } from "@/lib/backendApi";

type Identity = { id: string; nickname?: string | null; email?: string | null; avatar_url?: string | null };

export default function ProfileScreen() {
  const session = useDemoSession();
  const [editing, setEditing] = useState(false);
  const [nickname, setNickname] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [user, setUser] = useState<Identity | null>(null);
  const [familyName, setFamilyName] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void Promise.all([
      backendApi.getMyIdentity(session.currentUserId),
      backendApi.listFamilies(session.currentUserId)
    ]).then(([identity, families]) => {
      if (!active) return;
      setUser(identity);
      setNickname(identity.nickname ?? "");
      setFamilyName(families[0]?.name ?? null);
    }).catch(() => active && setUser(null));
    return () => { active = false; };
  }, [session.currentUserId, session.dataMode]);

  const avatarUrl = user?.avatar_url?.startsWith("http") ? user.avatar_url : user?.avatar_url ? `${session.apiBaseUrl}${user.avatar_url}` : undefined;

  async function chooseAvatar() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("需要相册权限", "允许访问相册后，才能选择个人头像。");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({ allowsEditing: true, aspect: [1, 1], mediaTypes: ["images"], quality: 0.85 });
    if (result.canceled) return;
    const asset = result.assets[0];
    setUploading(true);
    try {
      const response = await fetch(asset.uri);
      const content = await response.blob();
      setUser(await backendApi.uploadMyAvatar({ content, mimeType: asset.mimeType ?? content.type ?? "image/jpeg" }, session.currentUserId));
    } catch {
      Alert.alert("头像上传失败", "请检查网络后重试。");
    } finally {
      setUploading(false);
    }
  }

  async function saveNickname() {
    const value = nickname.trim();
    if (!value) return;
    setSaving(true);
    try {
      setUser(await backendApi.updateMyIdentity({ nickname: value }, session.currentUserId));
      setEditing(false);
    } catch {
      Alert.alert("昵称保存失败", "请稍后重试。");
    } finally {
      setSaving(false);
    }
  }

  return <AppScreen>
    <ArchiveSubHeader title="个人资料" />
    <CardBase style={styles.profileCard}>
      <Pressable accessibilityHint="选择后可裁剪为正方形，页面会以圆形头像显示" onPress={() => void chooseAvatar()} style={styles.avatar}>
        {avatarUrl ? <Image source={{ uri: avatarUrl }} style={styles.avatarImage} /> : <Text style={styles.avatarText}>👤</Text>}
        <View style={styles.avatarEdit}><Ionicons color="#FFFFFF" name="camera" size={12} /></View>
      </Pressable>
      <View style={styles.profileCopy}>
        <View style={styles.nameRow}><Text style={styles.name}>{user?.nickname ?? session.authSession.user?.nickname ?? "未命名用户"}</Text><StatusBadge label="当前用户" tone="mint" /></View>
        <Text style={styles.description}>{uploading ? "正在上传头像…" : "点击头像从相册选择；裁剪框为 1:1，头像将以圆形显示。"}</Text>
      </View>
    </CardBase>

    <CardBase style={styles.groupCard}>
      <View style={styles.headingRow}><Text style={styles.heading}>基础资料</Text><Pressable disabled={saving} onPress={() => editing ? void saveNickname() : setEditing(true)}><Text style={styles.edit}>{editing ? (saving ? "保存中…" : "保存") : "编辑"}</Text></Pressable></View>
      <View style={styles.row}>
        <View style={styles.iconWrap}><Ionicons color={theme.colors.primary} name="person-outline" size={18} /></View><Text style={styles.label}>昵称</Text>
        {editing ? <TextInput autoFocus maxLength={40} onChangeText={setNickname} style={styles.nicknameInput} value={nickname} /> : <Text style={styles.value}>{user?.nickname ?? "未填写"}</Text>}
      </View>
      <View style={[styles.row, styles.lastRow]}><View style={styles.iconWrap}><Ionicons color={theme.colors.primary} name="mail-outline" size={18} /></View><Text style={styles.label}>邮箱</Text><Text style={styles.value}>{user?.email ?? "未填写"}</Text></View>
    </CardBase>

    <CardBase style={styles.groupCard}>
      <Text style={styles.heading}>健康档案关联</Text>
      <View style={[styles.infoRow, styles.lastInfo]}><Ionicons color={theme.colors.primary} name="home-outline" size={19} /><View style={styles.infoCopy}><Text style={styles.label}>当前家庭</Text><Text style={styles.value}>{familyName ?? "暂未加入家庭"}</Text></View></View>
    </CardBase>
    <Text style={styles.note}>家庭身份和健康资料共享范围请在家庭档案中管理。</Text>
  </AppScreen>;
}

const styles = StyleSheet.create({
  avatar: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 34, height: 68, justifyContent: "center", width: 68 },
  avatarText: { fontSize: 40 }, avatarImage: { borderRadius: 34, height: 68, width: 68 },
  avatarEdit: { alignItems: "center", backgroundColor: theme.colors.primary, borderColor: "#FFFFFF", borderRadius: 12, borderWidth: 2, bottom: -2, height: 24, justifyContent: "center", position: "absolute", right: -2, width: 24 },
  description: { color: theme.colors.subtle, fontSize: 13, lineHeight: 19, marginTop: 5 }, edit: { color: theme.colors.primaryDark, fontSize: 13, fontWeight: "900" },
  groupCard: { paddingBottom: 0, paddingTop: 13 }, heading: { color: theme.colors.ink, fontSize: 17, fontWeight: "900" }, headingRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", paddingBottom: 4 },
  iconWrap: { alignItems: "center", backgroundColor: theme.colors.coralSoft, borderRadius: 10, height: 33, justifyContent: "center", width: 33 },
  infoCopy: { flex: 1, flexDirection: "row", justifyContent: "space-between" }, infoRow: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 10, paddingVertical: 13 },
  label: { color: theme.colors.subtle, fontSize: 13 }, lastInfo: { borderBottomWidth: 0 }, lastRow: { borderBottomWidth: 0 }, name: { color: theme.colors.ink, fontSize: 20, fontWeight: "900" }, nameRow: { alignItems: "center", flexDirection: "row", flexWrap: "wrap", gap: 8 },
  nicknameInput: { borderBottomColor: theme.colors.primary, borderBottomWidth: 1, color: theme.colors.ink, fontSize: 13, fontWeight: "700", marginLeft: "auto", minWidth: 120, paddingVertical: 2, textAlign: "right" },
  note: { color: theme.colors.subtle, fontSize: 12, lineHeight: 19, paddingHorizontal: 4 }, profileCard: { alignItems: "center", backgroundColor: theme.colors.blueSoft, flexDirection: "row", gap: 14 }, profileCopy: { flex: 1 },
  row: { alignItems: "center", borderBottomColor: theme.colors.line, borderBottomWidth: 1, flexDirection: "row", gap: 10, paddingVertical: 12 }, value: { color: theme.colors.ink, fontSize: 13, fontWeight: "700", marginLeft: "auto" }
});
