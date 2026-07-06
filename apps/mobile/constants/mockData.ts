export type MemberId = "me" | "dad" | "mom";

export const currentUser = {
  id: "me",
  name: "Gala",
  badge: "当前 Demo 用户",
  familyName: "幸福一家"
};

export const family = {
  id: "family-demo",
  name: "幸福一家",
  summary: "3 位成员 · 共同守护家人健康",
  invitationCode: "FAMILY-HEALTH"
};

export const members = [
  {
    id: "me" as MemberId,
    name: "我",
    relation: "家庭成员（我）",
    avatar: "👩🏻",
    cardTone: "mint",
    status: "暂无新记录",
    secondaryStatus: "有待确认草稿",
    recentRecord: "症状记录 · 头痛，5 月14日",
    shareStatus: "已共享全部健康记录"
  },
  {
    id: "dad" as MemberId,
    name: "爸爸",
    relation: "家庭成员（父亲）",
    avatar: "👨🏻",
    cardTone: "blue",
    status: "最近血压已记录",
    secondaryStatus: "已共享部分健康记录",
    recentRecord: "血压 120/78 mmHg，今天 07:30",
    shareStatus: "已共享部分健康记录"
  },
  {
    id: "mom" as MemberId,
    name: "妈妈",
    relation: "家庭成员（母亲）",
    avatar: "👩🏻‍🦰",
    cardTone: "orange",
    status: "有 1 个复查提醒",
    secondaryStatus: "已共享部分健康记录",
    recentRecord: "复查提醒，5 月20日",
    shareStatus: "已共享部分健康记录"
  }
];

export const todos = [
  {
    id: "todo-bp",
    icon: "heart-outline",
    title: "爸爸 · 记录今日血压",
    description: "建议每天早晚各记录一次",
    action: "去记录",
    tone: "mint"
  },
  {
    id: "todo-review",
    icon: "notifications-outline",
    title: "妈妈 · 复查提醒",
    description: "甲状腺复查 · 5 月20日",
    action: "去确认",
    tone: "orange"
  },
  {
    id: "todo-draft",
    icon: "clipboard-outline",
    title: "你有待确认的草稿",
    description: "症状草稿 · 1 条",
    action: "去确认",
    tone: "purple"
  }
];

export const recentActivities = [
  "爸爸 记录了血压 · 今天 07:30",
  "妈妈 新增了复查提醒 · 昨天 20:10",
  "Gala 保存了症状草稿 · 5 月14日"
];

export const quickActions = [
  { id: "bp", label: "记录血压", icon: "pulse-outline", href: "/create-symptom-draft" },
  { id: "symptom", label: "记录症状", icon: "sad-outline", href: "/create-symptom-draft" },
  { id: "alert", label: "创建提醒", icon: "calendar-outline", href: "/create-alert" },
  { id: "event", label: "添加健康事件", icon: "documents-outline", href: "/create-symptom-draft" }
] as const;

export const agentActions = [
  {
    id: "brief",
    workflowType: "daily_health_brief",
    title: "今日健康简报",
    description: "生成全家健康记录快照",
    href: "/agent-brief",
    icon: "newspaper-outline",
    tone: "blue"
  },
  {
    id: "symptomDraft",
    workflowType: "symptom_draft_create",
    title: "创建症状草稿",
    description: "根据记录生成待确认草稿",
    href: "/create-symptom-draft",
    icon: "person-circle-outline",
    tone: "purple"
  },
  {
    id: "eventDraft",
    workflowType: "medical_event_draft_create",
    title: "创建健康事件草稿",
    description: "整理记录生成事件草稿",
    href: "/create-symptom-draft",
    icon: "calendar-number-outline",
    tone: "mint"
  },
  {
    id: "alertCreate",
    workflowType: "alert_create",
    title: "创建健康提醒",
    description: "根据记录与习惯建议生成提醒计划",
    href: "/create-alert",
    icon: "notifications-outline",
    tone: "orange"
  }
] as const;

export const pendingDrafts = [
  {
    id: "draft-symptom-1",
    type: "症状草稿",
    title: "头痛、乏力",
    createdAt: "5 月14日 10:30",
    summary: "用户确认前仅作为草稿保存，不进入正式健康事实。",
    status: "待确认"
  },
  {
    id: "draft-event-1",
    type: "健康事件草稿",
    title: "体检",
    createdAt: "5 月13日 16:20",
    summary: "整理体检相关记录，等待补充与确认。",
    status: "待确认"
  }
];

export const reminders = [
  {
    id: "reminder-1",
    title: "爸爸今晚量血压",
    time: "今天 20:30",
    member: "爸爸",
    note: "普通家庭健康提醒，不是急救服务。"
  },
  {
    id: "reminder-2",
    title: "妈妈复查日程",
    time: "5 月20日 09:00",
    member: "妈妈",
    note: "提醒携带既往资料。"
  }
];

export const agentLogs = [
  {
    id: "log-1",
    title: "生成今日健康简报",
    time: "今天 07:35",
    status: "已完成"
  },
  {
    id: "log-2",
    title: "创建症状草稿：头痛、乏力",
    time: "5 月14日 10:30",
    status: "等待确认"
  }
];

export const agentRun = {
  id: "run-12",
  workflowType: "daily_health_brief",
  status: "completed",
  generatedContent:
    "根据系统内记录，已为你整理最近 7 天的家庭健康简报。本简报不能替代医生诊断或治疗建议。如有不适或紧急情况，请联系医生或当地急救服务。",
  toolCalls: 5,
  safetyChecks: "通过"
};

export const toolCalls = [
  { id: "tool-1", name: "health_profile.get", status: "completed", summary: "读取健康档案摘要" },
  { id: "tool-2", name: "health_data.blood_pressure.summary", status: "completed", summary: "整理血压记录数量" },
  { id: "tool-3", name: "health_record.symptoms.summary", status: "completed", summary: "整理症状记录摘要" },
  { id: "tool-4", name: "medical_timeline.followups.list", status: "completed", summary: "读取待随访事件" },
  { id: "tool-5", name: "alerts.active.list", status: "completed", summary: "读取 active reminders 数量" }
];

export const safetyChecks = [
  { id: "safety-1", stage: "input", status: "passed", summary: "未发现禁止类请求" },
  { id: "safety-2", stage: "output", status: "passed", summary: "输出保持整理与提醒边界" }
];

export const settingsGroups = [
  [
    { title: "个人资料", description: "管理个人信息与账号", icon: "person-outline" },
    { title: "通知设置", description: "管理提醒与消息通知", icon: "notifications-outline" }
  ],
  [
    { title: "家庭共享设置", description: "管理家庭成员与共享权限", icon: "people-outline" },
    { title: "隐私设置", description: "隐私与数据保护选项", icon: "shield-checkmark-outline" }
  ],
  [
    { title: "数据来源", description: "查看与管理数据来源", icon: "server-outline" },
    { title: "开发者调试", description: "日志、工具与调试选项", icon: "construct-outline" }
  ],
  [{ title: "关于 App", description: "版本信息与帮助中心", icon: "information-circle-outline" }]
];

export const dataSources = [
  "手动记录",
  "表格导入：后续",
  "健康设备：后续",
  "医疗文档：后续"
];
