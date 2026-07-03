from __future__ import annotations


def symptom_fields_from_draft(extracted_json: dict) -> dict:
    symptom = extracted_json.get("symptom")
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
