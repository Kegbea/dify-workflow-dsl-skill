# Dify Workflow DSL Skill

[English](README.md)

这是一个可移植的 Agent Skill，用于根据自然语言需求创建、修改、修复、审查和校验 Dify `workflow` 与 `advanced-chat` App DSL YAML。

## 能力

- 根据业务是否需要多轮上下文，在 Workflow 与 Chatflow 之间选择。
- 生成前规划节点输入输出、分支、失败路径和依赖。
- 按 Dify 版本、应用模式和节点类型加载对应规范。
- 检查图结构、变量引用、分支句柄、Code 节点、依赖和疑似明文密钥。
- 提供两种模式的最小模板及脱敏复杂示例。

## 兼容基线

| 组件 | 基线 |
|---|---|
| Skill | `0.1.0` |
| Dify | `1.17.x` |
| App DSL | `0.7.0` |
| Python | `3.9+` |
| 运行依赖 | `PyYAML 6.x` |

这个版本号是默认生成目标，不代表所有动态节点都能跨工作区直接使用。模型、插件、工具、知识库、Human Input、触发器和 Agent 节点可能包含工作区专属字段；目标 Dify 工作区的最新导出始终具有更高参考优先级。

## 安装

```bash
git clone https://github.com/Kegbea/dify-workflow-dsl-skill.git
cp -R dify-workflow-dsl-skill ~/.codex/skills/dify-workflow-dsl
```

Windows PowerShell：

```powershell
git clone https://github.com/Kegbea/dify-workflow-dsl-skill.git
Copy-Item -Recurse -Force dify-workflow-dsl-skill "$HOME/.codex/skills/dify-workflow-dsl"
```

必须保留完整目录，因为 `SKILL.md` 会使用 `references/`、`assets/` 和 `scripts/`。复制后重新加载或重启 Agent。

其他编程 Agent 只有在支持 `SKILL.md` 类 Skill、能够读取本地文件并执行 Python 时才能自动使用；否则需要明确要求 Agent 先读取 `SKILL.md`。不同 Agent 的自动发现机制并不完全相同。

## 使用

```text
使用 $dify-workflow-dsl 创建一个 Dify Workflow：接收订单号、调用 HTTP API、判断风险并返回严格 JSON。
```

```text
使用 $dify-workflow-dsl 创建一个多轮智能客服 Chatflow：包含对话记忆、知识库检索、文件上传和兜底回复。
```

## 示例

[`examples/`](examples/README.md) 包含脱敏后的复杂 Workflow 和 Chatflow。所有以 `REPLACE_WITH_` 开头的值都是工作区绑定占位符，导入前必须替换。

## 校验

```bash
python -m pip install -r requirements.txt
python scripts/validate_dsl.py --strict --target-version 0.7.0 path/to/app.yml
python -m unittest discover -s tests -p "test_*.py" -v
```

静态校验不能代替 Dify 导入、预览和实际渠道冒烟测试。

## 生成发布包

```bash
python scripts/package_release.py
```

发布包生成在 `dist/`，ZIP 内包含顶层目录 `dify-workflow-dsl/`。压缩包默认不会提交到 Git。

## 能力边界

本 Skill 可以提升 DSL 生成一致性并发现大量静态问题，但不能承诺任意复杂工作流在所有 Dify 环境中直接运行。最终结果仍受插件、凭据、模型能力、知识库绑定、外部 API 和 Dify 版本影响。

公开示例中不得包含真实 API Key、Token、私有接口、客户数据或私有知识库标识，应使用环境变量或明确占位符。

## 参与贡献

贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，安全问题见 [SECURITY.md](SECURITY.md)，版本变化见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

使用 MIT License，详见 [LICENSE](LICENSE)。相关项目说明见 [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md)。
