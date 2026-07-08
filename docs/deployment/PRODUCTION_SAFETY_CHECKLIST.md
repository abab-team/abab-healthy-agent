# 生产安全检查清单

Phase 15 当前只完成 MVP 演示部署收口，不代表正式生产上线。生产前必须逐项复核。

## 认证与密钥

- [ ] `AUTH_DEMO_HEADER_ENABLED=false`
- [ ] `AUTH_ENABLED=true`
- [ ] `JWT_SECRET_KEY` 使用强随机值
- [ ] `SECRET_KEY` 使用强随机值
- [ ] `.env` 不提交
- [ ] API key、OCR key、embedding key、JWT secret 不提交
- [ ] 移动端生产包使用安全 token 存储方案，Native 环境补充 SecureStore 或等价能力

## 网络与 CORS

- [ ] `DEBUG=false`
- [ ] CORS 只允许明确域名
- [ ] 使用 HTTPS
- [ ] 防火墙仅开放必要端口
- [ ] 管理端/调试端口不暴露公网

## 数据库

- [ ] 生产使用 PostgreSQL 或等价持久化数据库
- [ ] migration 通过
- [ ] 数据库备份策略明确
- [ ] seed demo data 不写入生产库
- [ ] demo 用户与 demo 密码不进入生产

## 文件与 OCR

- [ ] storage 目录或对象存储持久化
- [ ] 上传文件不提交 Git
- [ ] API 不返回本机绝对路径或 `file_path`
- [ ] 真实 OCR provider 接入前完成安全 review
- [ ] raw OCR 存储默认关闭，若开启需完成隐私与保留策略 review
- [ ] 生产文件建议补充病毒扫描、对象存储 ACL、加密和保留策略

## LLM / RAG / Agent

- [ ] `LLM_ENABLED` 默认关闭或受控开启
- [ ] `DAILY_BRIEF_USE_LLM` 仅在安全评估后开启
- [ ] `RAG_ENABLED` 默认关闭或受控开启
- [ ] 不接外部医学知识库，除非完成来源、引用、合规与安全 review
- [ ] 不开放通用 tool execution
- [ ] 不允许前端传 `tool_name` / `input_data`
- [ ] LLM/RAG/OCR 不直接写正式健康事实
- [ ] Agent 写入动作继续经过 preview / confirm
- [ ] trace/debug 不记录 raw prompt、raw response、raw OCR、file path、token、key

## 医疗安全边界

- [ ] 不输出医学诊断
- [ ] 不输出处方建议
- [ ] 不输出剂量建议
- [ ] 不输出停药/换药建议
- [ ] 不承诺自动急救、自动报警、自动联系医院或家人
- [ ] 不把“系统内暂无记录”表达成现实身体无问题

## 发布前验收

- [ ] 后端 API tests 通过
- [ ] mobile typecheck / lint / export 通过
- [ ] smoke 脚本通过
- [ ] 真机 QA 完成
- [ ] README、runbook、QA 文档与实际能力一致

