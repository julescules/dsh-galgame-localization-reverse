# dsh-galgame-localization-reverse

中文 | [English](README.md)

> [!IMPORTANT]
> 非官方社区插件，由社区独立开发与维护，未经 DeepSeek 审核或背书。

面向 DeepSeek Harness 的 Galgame／视觉小说汉化与逆向工程 Skill Provider。

![从引擎证据到可回滚发布](docs/demo.svg)

## 能做什么

- 根据文件、魔数与运行证据识别 25 种以上视觉小说引擎家族；
- 为文本、图片、封包、字节码、字体和编码问题选择对应工作流；
- 保护占位符、控制码、源文件哈希、存档兼容性与回滚路径；
- 自带 `vn_qa.py`，检查占位符与目标编码；
- 自带 `vn_patch.py`，生成哈希绑定的替换补丁，并支持验证与回滚；
- 覆盖 AI6WIN、BGI/Ethornell、Director、RealLive、PSP/Vita 和自定义引擎。

## 安装

```powershell
dsh plugin --profile web add github:julescules/dsh-galgame-localization-reverse#v0.1.0
dsh --profile web --dump-config
```

安装后重启 DSH。插件会通过 `ctx.skills` 注册 `galgame-localization-reverse`，并让 Skill 能按需读取配套参考资料和脚本。

## 使用

要求 DSH 使用 `galgame-localization-reverse`，再提供游戏目录和目标。工作流会先做只读清单与引擎证据确认，再决定提取、写回和发布路线。

```text
请使用 galgame-localization-reverse 识别这个游戏的引擎，建立文本所有者清单，
并为 D:\Games\Example 设计可回滚的汉化流程。
```

## 自带工具

```powershell
python -X utf8 skill\scripts\vn_qa.py --selftest
python -X utf8 skill\scripts\vn_patch.py --selftest
```

仓库不包含游戏资源、解密封包、账号凭据或作品专用密钥。公开发布应只包含工具、清单、文档以及差分／替换补丁。

## 已验证

- 官方 Skill Provider 结构：`inject = ['skills']` 与 `ctx.skills.registerProvider`；
- 官方 `dsh.bundle.patch` 安装入口；
- YAML frontmatter 去除与 `resourceBase` 解析；
- Skill 直接引用的参考资料与脚本均存在；
- Node Provider 测试及两个 Python 工具自测；
- npm 包文件白名单与公开内容扫描。

```powershell
npm run check
npm pack --dry-run
```

## 边界

- 引擎格式和二进制常量在绑定具体版本哈希前都只是候选，不能跨作品照搬。
- 静态验证不能代替实际 UI、存读档、音频和回滚测试。
- DeepSeek Harness 尚处于开发预览阶段，建议固定到已审阅的插件版本。

## 许可

[MIT](LICENSE)
