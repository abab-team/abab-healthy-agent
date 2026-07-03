# 模块领域：核心基础设施层
# 领域说明：负责配置、环境、日志、异常等横切能力。
# 文件职责：日志文件。统一日志格式、级别和输出方式，便于排查问题和接入可观测系统。
# 维护原则：本文件只补充业务/工程注释，不在注释中改变任何运行逻辑。

import logging


# 函数职责：业务函数，封装 核心基础设施层 中的一段可复用逻辑。
# 业务边界：调用方应根据返回值和异常语义处理成功与失败。
def setup_logging(debug: bool = False) -> None:
    # 流程说明：
    # 1. 接收上游传入的数据或上下文。
    # 2. 完成本函数职责范围内的处理。
    # 3. 将结果返回给调用方，继续由上层流程编排。
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
