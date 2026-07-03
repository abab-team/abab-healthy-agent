# 模块领域：健康记录模块
# 领域说明：负责症状、用药、就医、备注等事件型健康记录。
# 文件职责：草稿解析文件。把自由文本健康记录转换为可确认的结构化草稿。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

from __future__ import annotations


# 函数职责：业务函数，封装 健康记录模块 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def symptom_fields_from_draft(extracted_json: dict) -> dict:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    symptom = extracted_json.get("symptom")
    # 分支说明：根据当前条件选择不同业务路径，保证异常场景和正常场景分开处理。
    if isinstance(symptom, dict):
        source = symptom
    else:
        source = extracted_json
    return {
        "symptom_name": source.get("symptom_name"),
        "body_part": source.get("body_part"),
        "severity": source.get("severity"),
        "duration_text": source.get("duration_text"),
        "occurrence_time_text": source.get("occurrence_time_text"),
        "possible_trigger": source.get("possible_trigger"),
        "related_metric_types": source.get("related_metric_types"),
        "action_taken": source.get("action_taken"),
        "follow_up_needed": bool(source.get("follow_up_needed", False)),
        "ai_summary": source.get("ai_summary"),
    }
