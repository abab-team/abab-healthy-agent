# Phase 14 RAG Evaluation

## 当前评估范围

Phase 14 只做最小合成评估，验证：

- simple retriever 可以优先返回与 query 匹配的内部安全摘要。
- source policy 可以拒绝敏感 marker。
- chunking 不丢失 citation / permission 元数据。
- RAG API 不返回 `file_path`、`raw_extracted_text`、token、password、API key。

## 运行命令

```powershell
$env:PYTHONPATH="backend"
python -m unittest discover backend/tests/rag -v
python -m unittest discover backend/tests/evaluation -v
python -m unittest backend.tests.api.test_rag_api -v
```

## 不在本阶段评估

- 真实 embedding provider。
- vector DB recall/precision。
- 外部医学知识库质量。
- RAG 问答质量。
- 医学结论正确性。

这些能力必须在后续单独 Phase 中经过 schema、权限、privacy、safety review。
