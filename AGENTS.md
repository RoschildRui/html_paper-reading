# AGENTS.md

## Commit 规范（Conventional Commits）

提交信息格式：

```
<type>(<scope>): <subject>
```

- `type`：必填，说明提交类型。
- `scope`：可选，说明影响范围（如某个论文目录 `deepseek`、`qwen`）。
- `subject`：必填，简洁描述本次改动，使用祈使句、首字母小写、结尾不加句号。

### type 取值

| type       | 说明                             |
| ---------- | -------------------------------- |
| `feat`     | 新增功能 / 新增论文可视化页面    |
| `fix`      | 修复问题                         |
| `docs`     | 文档改动（README、注释等）       |
| `style`    | 格式调整（不影响逻辑）           |
| `refactor` | 重构（非新增功能、非修复）       |
| `perf`     | 性能优化                         |
| `chore`    | 构建、配置、依赖等杂项           |

### 示例

```
feat(deepseek): add deepseek-r1 visual reading page
docs: update README overview
fix(qwen): correct broken image path
chore: add .gitignore
```

### 约定

- 一次提交只做一件事，保持提交粒度清晰。
- subject 尽量控制在 50 字符以内；如需详述，空一行后写正文。
- 主分支为 `main`。
