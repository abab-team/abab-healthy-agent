# 模块领域：家庭成员模块
# 领域说明：负责家庭、成员关系、邀请流程和自然语言成员称呼解析。
# 文件职责：成员解析文件。把“我爸/妈妈/本人”等自然语言称呼解析为系统成员。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations


REFERENCE_ALIASES: dict[str, list[str]] = {
    "self": ["我", "我自己", "本人"],
    "father": ["爸爸", "我爸", "父亲"],
    "mother": ["妈妈", "我妈", "母亲"],
    "spouse": ["配偶", "老婆", "老公"],
}


# 函数职责：解析流程，把外部输入、自然语言或原始字段转换为系统内部标准形式。
# 业务边界：解析结果只能作为候选或标准化结果，关键写入仍需权限和业务校验。
def normalize_member_reference(member_reference: str) -> str:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return member_reference.strip()


# 函数职责：业务函数，封装 家庭成员模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def relationship_labels_for_reference(member_reference: str) -> list[str]:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    normalized = normalize_member_reference(member_reference)
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if normalized in REFERENCE_ALIASES["father"]:
        return ["爸爸", "父亲"]
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if normalized in REFERENCE_ALIASES["mother"]:
        return ["妈妈", "母亲"]
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if normalized in REFERENCE_ALIASES["spouse"]:
        return ["配偶", "老婆", "老公"]
    return [normalized]


# 函数职责：业务函数，封装 家庭成员模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def is_self_reference(member_reference: str) -> bool:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    return normalize_member_reference(member_reference) in REFERENCE_ALIASES["self"]
