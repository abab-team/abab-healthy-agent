import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import * as ImagePicker from "expo-image-picker";
import { Link } from "expo-router";
import { useMemo, useState } from "react";
import { ActivityIndicator, Alert, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { CardBase } from "@/components/cards/CardBase";
import { ApiErrorState } from "@/components/common/ApiErrorState";
import { ArchiveSubHeader } from "@/components/common/ArchiveSubHeader";
import { SectionHeader } from "@/components/common/SectionHeader";
import { AppScreen } from "@/components/layout/AppScreen";
import { colors } from "@/constants/colors";
import { theme } from "@/constants/theme";
import { useApiResource } from "@/hooks/useApiResource";
import { useDemoSession } from "@/hooks/useDemoSession";
import { backendApi } from "@/lib/backendApi";
import { getDataProvider } from "@/lib/dataProvider";
import { routes } from "@/lib/routes";
import type { ApiResult, MedicalDocument } from "@/types/api";

type DocumentsProvider = {
  listDocuments: () => Promise<ApiResult<{ items: MedicalDocument[]; source: "mock" | "api"; mockSections: string[] }>>;
};

type UploadFile = {
  fileName: string;
  mimeType: "application/pdf" | "image/jpeg" | "image/png";
  size?: number | null;
  uri: string;
};

type DocumentTypeOption = {
  id: "checkup_report" | "medical_record" | "lab_test" | "prescription" | "other";
  label: string;
};

const documentTypes: DocumentTypeOption[] = [
  { id: "checkup_report", label: "体检报告" },
  { id: "medical_record", label: "检查报告" },
  { id: "lab_test", label: "化验单" },
  { id: "prescription", label: "病历 / 处方资料" },
  { id: "other", label: "其他资料" }
];

const allowedMimeTypes = ["application/pdf", "image/jpeg", "image/png"] as const;
const maxUploadBytes = 10 * 1024 * 1024;

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function defaultTitle(fileName: string): string {
  return fileName.replace(/\.[^.]+$/, "").trim() || "医疗资料";
}

function prettySize(size?: number | null): string {
  if (!size || size < 1024) return "大小未提供";
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function prettyDate(value?: string | null): string {
  if (!value) return "归档日期未提供";
  return value.slice(0, 10);
}

function typeLabel(value?: string | null): string {
  return documentTypes.find((item) => item.id === value)?.label ?? "医疗资料";
}

function normalizePickedFile(file: { mimeType?: string | null; name?: string | null; size?: number | null; uri: string }): UploadFile | null {
  const extension = (file.name ?? "").split(".").pop()?.toLowerCase();
  const mimeType = file.mimeType && allowedMimeTypes.includes(file.mimeType as (typeof allowedMimeTypes)[number])
    ? file.mimeType
    : extension === "pdf" ? "application/pdf" : extension === "png" ? "image/png" : ["jpg", "jpeg"].includes(extension ?? "") ? "image/jpeg" : "";
  if (!allowedMimeTypes.includes(mimeType as (typeof allowedMimeTypes)[number])) {
    return null;
  }
  return {
    fileName: file.name ?? `医疗资料.${mimeType === "application/pdf" ? "pdf" : mimeType === "image/png" ? "png" : "jpg"}`,
    mimeType: mimeType as UploadFile["mimeType"],
    size: file.size,
    uri: file.uri
  };
}

function uploadErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : "上传失败，请稍后重试。";
  const lower = message.toLowerCase();
  if (lower.includes("too large")) return "文件超过 10 MB，暂时无法归档。";
  if (lower.includes("unsupported")) return "暂只支持 PDF、JPG 和 PNG 文件。";
  if (lower.includes("network") || lower.includes("fetch")) return "网络不可用，资料尚未保存。";
  if (lower.includes("permission") || lower.includes("forbidden")) return "当前没有归档这份资料的权限。";
  return "上传未完成，资料尚未保存。请检查网络后重试。";
}

export default function DocumentsScreen() {
  const session = useDemoSession();
  const provider = getDataProvider(session.currentUserId) as DocumentsProvider;
  const documents = useApiResource(() => provider.listDocuments(), [session.currentUserId, session.dataMode]);
  const items = documents.data?.items ?? [];
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<UploadFile | null>(null);
  const [selectedType, setSelectedType] = useState<DocumentTypeOption>(documentTypes[0]);
  const [title, setTitle] = useState("");
  const [documentDate, setDocumentDate] = useState(today());
  const [uploading, setUploading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const canUpload = session.dataMode === "api";
  const currentTypeLabel = useMemo(() => selectedType.label, [selectedType]);

  const openUpload = () => {
    if (!canUpload) {
      Alert.alert("演示模式", "演示模式不会保存真实文件。切换到 API 数据模式后即可归档资料。");
      return;
    }
    setFormError(null);
    setSelectedFile(null);
    setTitle("");
    setDocumentDate(today());
    setModalVisible(true);
  };

  const usePickedFile = (file: UploadFile | null) => {
    if (!file) {
      setFormError("暂只支持 PDF、JPG 和 PNG 文件。");
      return;
    }
    if (file.size && file.size > maxUploadBytes) {
      setFormError("文件超过 10 MB，暂时无法归档。");
      return;
    }
    setSelectedFile(file);
    setTitle(defaultTitle(file.fileName));
    setFormError(null);
  };

  const selectDocument = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
      type: [...allowedMimeTypes]
    });
    if (result.canceled) return;
    usePickedFile(normalizePickedFile(result.assets[0]));
  };

  const selectFromLibrary = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setFormError("需要相册权限才能选择图片资料。");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.9 });
    if (result.canceled) return;
    const asset = result.assets[0];
    usePickedFile(normalizePickedFile({
      mimeType: asset.mimeType ?? "image/jpeg",
      name: asset.fileName ?? "检查资料.jpg",
      size: asset.fileSize,
      uri: asset.uri
    }));
  };

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      setFormError("需要相机权限才能拍照归档。");
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.9 });
    if (result.canceled) return;
    const asset = result.assets[0];
    usePickedFile(normalizePickedFile({
      mimeType: asset.mimeType ?? "image/jpeg",
      name: asset.fileName ?? "体检资料.jpg",
      size: asset.fileSize,
      uri: asset.uri
    }));
  };

  const saveDocument = async () => {
    if (!selectedFile) {
      setFormError("请先选择要归档的资料。");
      return;
    }
    if (!title.trim()) {
      setFormError("请填写资料标题。");
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(documentDate)) {
      setFormError("资料日期请使用 YYYY-MM-DD 格式。");
      return;
    }

    setUploading(true);
    setFormError(null);
    try {
      const fileResponse = await fetch(selectedFile.uri);
      const content = await fileResponse.blob();
      await backendApi.uploadMyDocument({
        content,
        documentType: selectedType.id,
        fileName: selectedFile.fileName,
        mimeType: selectedFile.mimeType,
        title: title.trim()
      }, session.currentUserId);
      setModalVisible(false);
      await documents.reload();
      Alert.alert("已归档", "资料已保存到医疗资料中，当前不会自动解读内容。");
    } catch (error) {
      setFormError(uploadErrorMessage(error));
    } finally {
      setUploading(false);
    }
  };

  return (
    <AppScreen>
      <ArchiveSubHeader title="医疗资料与就医历史" />
      <CardBase style={styles.uploadCard}>
        <View style={styles.uploadIcon}><Ionicons color={theme.colors.primary} name="cloud-upload-outline" size={24} /></View>
        <Text style={styles.uploadTitle}>医疗资料与就医历史</Text>
        <Text style={styles.copy}>保存体检报告、检查资料和就医相关文件。</Text>
        <Pressable accessibilityRole="button" onPress={openUpload} style={styles.uploadButton}>
          <Ionicons color="#FFFFFF" name="add" size={19} />
          <Text style={styles.uploadButtonText}>上传体检报告 / 检查资料</Text>
        </Pressable>
        <Text style={styles.uploadHint}>支持照片和 PDF 文档，仅用于安全收纳与归档。</Text>
      </CardBase>

      {documents.loading ? <Text style={styles.loading}>正在读取资料列表...</Text> : null}
      {documents.error ? <ApiErrorState message={documents.error} /> : null}

      <CardBase>
        <SectionHeader title="已归档资料" action={`${items.length} 份`} />
        {items.length === 0 && !documents.loading ? (
          <View style={styles.empty}>
            <Ionicons color={theme.colors.subtle} name="folder-open-outline" size={28} />
            <Text style={styles.emptyTitle}>还没有医疗资料</Text>
            <Text style={styles.emptyCopy}>上传后可在这里安全查看已归档的文件信息。</Text>
          </View>
        ) : null}
        {items.map((item) => (
          <Link key={item.id} href={routes.documentDetail(item.id)} asChild>
            <Pressable style={styles.row}>
              <View style={styles.fileIcon}><Ionicons color="#E96A5D" name={item.file_mime_type?.startsWith("image/") ? "image-outline" : "document-text-outline"} size={20} /></View>
              <View style={styles.rowCopy}>
                <Text numberOfLines={1} style={styles.name}>{item.title}</Text>
                <Text numberOfLines={1} style={styles.meta}>{typeLabel(item.document_type)} · {prettyDate(item.document_date ?? item.created_at)} · {prettySize(item.file_size)}</Text>
              </View>
              <Text style={styles.archived}>已归档</Text>
              <Ionicons color={theme.colors.subtle} name="chevron-forward" size={18} />
            </Pressable>
          </Link>
        ))}
      </CardBase>

      <CardBase style={styles.notice}>
        <Ionicons color={theme.colors.primaryDark} name="shield-checkmark-outline" size={20} />
        <Text style={styles.noticeText}>资料仅用于保存与归档，当前不会自动解读内容。</Text>
      </CardBase>

      <Modal animationType="slide" onRequestClose={() => !uploading && setModalVisible(false)} transparent visible={modalVisible}>
        <View style={styles.modalBackdrop}>
          <View style={styles.sheet}>
            <View style={styles.sheetHandle} />
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>上传医疗资料</Text>
              <Pressable disabled={uploading} hitSlop={10} onPress={() => setModalVisible(false)}><Ionicons color={theme.colors.subtle} name="close" size={24} /></Pressable>
            </View>
            <ScrollView contentContainerStyle={styles.sheetContent} showsVerticalScrollIndicator={false}>
              <Text style={styles.fieldLabel}>选择文件来源</Text>
              <View style={styles.sourceGrid}>
                <SourceButton icon="camera-outline" label="拍照" onPress={() => void takePhoto()} />
                <SourceButton icon="images-outline" label="从相册选择" onPress={() => void selectFromLibrary()} />
                <SourceButton icon="document-attach-outline" label="选择文件" onPress={() => void selectDocument()} />
              </View>
              <Text style={styles.sourceHint}>目前可归档 JPG、PNG 和 PDF。Word 文档将于后续版本支持。</Text>

              {selectedFile ? (
                <View style={styles.filePreview}>
                  <Ionicons color={theme.colors.primary} name="document-outline" size={22} />
                  <View style={styles.rowCopy}><Text numberOfLines={1} style={styles.name}>{selectedFile.fileName}</Text><Text style={styles.meta}>{prettySize(selectedFile.size)}</Text></View>
                  <Pressable onPress={() => setSelectedFile(null)}><Ionicons color={theme.colors.subtle} name="close-circle-outline" size={21} /></Pressable>
                </View>
              ) : <Text style={styles.noFile}>请先选择一份资料。</Text>}

              <Text style={styles.fieldLabel}>归档信息</Text>
              <Text style={styles.inputLabel}>资料类型</Text>
              <View style={styles.typeOptions}>
                {documentTypes.map((item) => (
                  <Pressable key={item.label} onPress={() => setSelectedType(item)} style={[styles.typeOption, item.label === currentTypeLabel ? styles.typeOptionActive : null]}>
                    <Text style={[styles.typeOptionText, item.label === currentTypeLabel ? styles.typeOptionTextActive : null]}>{item.label}</Text>
                  </Pressable>
                ))}
              </View>
              <Text style={styles.inputLabel}>资料日期</Text>
              <TextInput autoCapitalize="none" onChangeText={setDocumentDate} placeholder="YYYY-MM-DD" style={styles.input} value={documentDate} />
              <Text style={styles.inputHint}>默认当前日期；可填写历史日期。当前上传接口以归档时间作为资料列表日期。</Text>
              <Text style={styles.inputLabel}>标题</Text>
              <TextInput onChangeText={setTitle} placeholder="资料标题" style={styles.input} value={title} />
              <Text style={styles.inputLabel}>归属成员</Text>
              <View style={styles.memberField}><Ionicons color={theme.colors.primary} name="person-outline" size={18} /><Text style={styles.memberText}>本人</Text><Text style={styles.memberHint}>当前仅支持归档到本人资料</Text></View>

              {formError ? <Text style={styles.formError}>{formError}</Text> : null}
              <Pressable accessibilityRole="button" disabled={uploading} onPress={() => void saveDocument()} style={[styles.saveButton, uploading ? styles.saveButtonDisabled : null]}>
                {uploading ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.saveButtonText}>保存到医疗资料</Text>}
              </Pressable>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </AppScreen>
  );
}

function SourceButton({ icon, label, onPress }: { icon: keyof typeof Ionicons.glyphMap; label: string; onPress: () => void }) {
  return <Pressable onPress={onPress} style={styles.sourceButton}><Ionicons color={theme.colors.primary} name={icon} size={23} /><Text style={styles.sourceButtonText}>{label}</Text></Pressable>;
}

const styles = StyleSheet.create({
  archived: { backgroundColor: theme.colors.tealSoft, borderRadius: 999, color: theme.colors.primaryDark, fontSize: 11, fontWeight: "800", overflow: "hidden", paddingHorizontal: 8, paddingVertical: 4 },
  copy: { color: theme.colors.subtle, fontSize: 14, lineHeight: 21, marginTop: 5 },
  empty: { alignItems: "center", gap: 6, paddingVertical: 28 },
  emptyCopy: { color: theme.colors.subtle, fontSize: 13, textAlign: "center" },
  emptyTitle: { color: theme.colors.ink, fontSize: 15, fontWeight: "800", marginTop: 3 },
  fieldLabel: { color: theme.colors.ink, fontSize: 17, fontWeight: "900", marginTop: 8 },
  fileIcon: { alignItems: "center", backgroundColor: "#FFF0ED", borderRadius: 10, height: 40, justifyContent: "center", width: 40 },
  filePreview: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 14, flexDirection: "row", gap: 10, marginTop: 12, padding: 12 },
  formError: { color: "#C44B45", fontSize: 13, lineHeight: 19, marginTop: 6 },
  input: { backgroundColor: theme.colors.canvas, borderColor: theme.colors.line, borderRadius: 12, borderWidth: 1, color: theme.colors.ink, fontSize: 15, marginTop: 6, paddingHorizontal: 12, paddingVertical: 12 },
  inputHint: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 5 },
  inputLabel: { color: theme.colors.ink, fontSize: 13, fontWeight: "800", marginTop: 15 },
  loading: { color: theme.colors.subtle, fontSize: 13, paddingHorizontal: 4 },
  memberField: { alignItems: "center", backgroundColor: theme.colors.canvas, borderColor: theme.colors.line, borderRadius: 12, borderWidth: 1, flexDirection: "row", gap: 8, marginTop: 6, padding: 12 },
  memberHint: { color: theme.colors.subtle, fontSize: 12, marginLeft: "auto" },
  memberText: { color: theme.colors.ink, fontSize: 14, fontWeight: "800" },
  meta: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 3 },
  modalBackdrop: { backgroundColor: "rgba(10, 28, 24, 0.34)", flex: 1, justifyContent: "flex-end" },
  name: { color: theme.colors.ink, fontSize: 15, fontWeight: "800" },
  noFile: { color: theme.colors.subtle, fontSize: 13, marginTop: 12 },
  notice: { alignItems: "center", backgroundColor: theme.colors.tealSoft, flexDirection: "row", gap: 10 },
  noticeText: { color: theme.colors.primaryDark, flex: 1, fontSize: 13, fontWeight: "700", lineHeight: 19 },
  row: { alignItems: "center", borderTopColor: theme.colors.line, borderTopWidth: 1, flexDirection: "row", gap: 10, paddingVertical: 12 },
  rowCopy: { flex: 1, minWidth: 0 },
  saveButton: { alignItems: "center", backgroundColor: theme.colors.primary, borderRadius: theme.radius.md, justifyContent: "center", marginTop: 18, minHeight: 48 },
  saveButtonDisabled: { opacity: 0.65 },
  saveButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "900" },
  sheet: { backgroundColor: theme.colors.surface, borderTopLeftRadius: 26, borderTopRightRadius: 26, maxHeight: "91%", paddingHorizontal: theme.spacing.lg, paddingTop: 10 },
  sheetContent: { gap: 4, paddingBottom: 30 },
  sheetHandle: { alignSelf: "center", backgroundColor: "#DCE7E2", borderRadius: 999, height: 4, width: 42 },
  sheetHeader: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", paddingBottom: 12, paddingTop: 13 },
  sheetTitle: { color: theme.colors.ink, fontSize: 19, fontWeight: "900" },
  sourceButton: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 14, flex: 1, gap: 6, minHeight: 80, justifyContent: "center", paddingHorizontal: 4 },
  sourceButtonText: { color: theme.colors.primaryDark, fontSize: 12, fontWeight: "800", textAlign: "center" },
  sourceGrid: { flexDirection: "row", gap: 9, marginTop: 9 },
  sourceHint: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 9 },
  typeOption: { backgroundColor: theme.colors.canvas, borderColor: theme.colors.line, borderRadius: 999, borderWidth: 1, paddingHorizontal: 11, paddingVertical: 8 },
  typeOptionActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
  typeOptionText: { color: theme.colors.subtle, fontSize: 12, fontWeight: "800" },
  typeOptionTextActive: { color: "#FFFFFF" },
  typeOptions: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 7 },
  uploadButton: { alignItems: "center", alignSelf: "flex-start", backgroundColor: theme.colors.primary, borderRadius: theme.radius.pill, flexDirection: "row", gap: 6, marginTop: 15, paddingHorizontal: 14, paddingVertical: 11 },
  uploadButtonText: { color: "#FFFFFF", fontSize: 14, fontWeight: "900" },
  uploadCard: { backgroundColor: "#FFFFFF" },
  uploadHint: { color: theme.colors.subtle, fontSize: 12, lineHeight: 18, marginTop: 10 },
  uploadIcon: { alignItems: "center", backgroundColor: theme.colors.tealSoft, borderRadius: 14, height: 48, justifyContent: "center", width: 48 },
  uploadTitle: { color: theme.colors.ink, fontSize: 19, fontWeight: "900", marginTop: 12 }
});
