# DeepSeek Harness Galgame Doctor

中文 | [English](README.md)

> [!IMPORTANT]
> 非官方社区插件，由社区独立开发与维护，未经 DeepSeek 审核或背书。

先体检，再汉化。把视觉小说目录交给 DeepSeek Harness，得到带证据的引擎候选、风险文件、编码线索、严格翻译 QA 和安全下一步。体检完全离线且只读；只允许把报告写到被审计目录之外。

![合成终端示例：只读引擎体检与严格翻译 QA](docs/demo.svg)

## 30 秒开始

```powershell
dsh plugin --profile web add github:julescules/dsh-galgame-localization-reverse#v0.4.0
```

重启 DSH，然后直接说：

```text
请使用 galgame-localization-reverse 对 D:\Games\Example 做只读体检，
列出引擎证据、汉化风险和最安全的下一步。
```

不需要 API Key。插件不包含游戏资源、解密封包、凭据或作品专用密钥。

## 能得到什么

### 一条命令完成项目体检

`vn_project_audit.py` 在受限范围内盘点文件，并报告：

- 带置信度、信号组和实际相对路径证据的引擎候选；
- 剧本、封包、图片、字体和可执行文件候选；
- 有上限的编码抽样，以及安全显示的中文／日文路径；
- 谨慎的 `candidate`、`weak-candidate` 或 `unknown` 分类；
- 下一步应查阅的参考、可复用的社区工具和验证动作。

分类只用于选择路线，不代表静态检查已经证明运行时行为。

```powershell
python -X utf8 skill\scripts\vn_project_audit.py scan D:\Games\Example `
  --json D:\project\logs\project-audit.json `
  --markdown D:\project\logs\project-audit.md
```

### 严格翻译门禁

`vn_qa.py` 现在默认阻断控制标记缺失、新增或重排，并检查空译、译文与原文相同、残留日文及目标编码失败。无需第三方包即可读取通用 JSON/JSONL 和 GalTransl 缓存字段。

```powershell
python -X utf8 skill\scripts\vn_qa.py check-jsonl D:\project\translations.jsonl `
  --encoding gbk --require-complete `
  --report D:\project\logs\translation-qa.json `
  --markdown D:\project\logs\translation-qa.md
```

仓库内故意损坏的合成样例会产生直观报告：

```text
FAIL  2 blockers · 3 segments
E control-token-added  scene01:2  added [wait]
E empty-translation    scene01:3  translation required
```

### 发布证据，而不是再造一个翻译器

插件还自带：

- `vn_patch.py`：哈希绑定的文件替换、验证、备份与回滚；
- `vn_image_qa.py`：比较 PNG/APNG、JPEG、GIF、BMP 的尺寸、alpha 和帧数；
- `vn_slot_qa.py`：检查固定槽终止符、填充、控制标记和槽区外改动；
- 面向 AI6WIN、BGI/Ethornell、Director、RealLive、Delphi/DirectDraw、PSP/Vita、Ren'Py、KiriKiri 和自定义引擎的专门路线。

GalTransl、VNTextPatch、GARbro、LunaTranslator 和引擎专用工具负责翻译或提取；Galgame Doctor 负责判断项目像什么、检查它们的文本输出，并保存可审计的发布证据。

## 运行合成样例

```powershell
python -X utf8 skill\scripts\vn_project_audit.py scan examples\synthetic-project\game `
  --json test_outputs\synthetic-audit.json `
  --markdown test_outputs\synthetic-audit.md

python -X utf8 skill\scripts\vn_qa.py check-jsonl examples\translations.jsonl `
  --encoding gbk --require-complete `
  --report test_outputs\translation-qa.json `
  --markdown test_outputs\translation-qa.md
```

所有示例文本均为原创合成数据，可公开再分发。

## DSH 集成方式

插件使用官方打包 Skill Provider 结构：

- `inject = ['skills']`；
- `ctx.skills.registerProvider(...)`；
- 通过目录 `resourceBase` 按需读取参考和脚本；
- 使用官方 `dsh.bundle.patch` 安装入口。

注册名仍是 `galgame-localization-reverse`，已有提示词无需修改。

## 验证包

[![CI](https://github.com/julescules/dsh-galgame-localization-reverse/actions/workflows/ci.yml/badge.svg)](https://github.com/julescules/dsh-galgame-localization-reverse/actions/workflows/ci.yml)

```powershell
npm run check
npm pack --dry-run
```

检查包含 Provider 测试，以及项目体检和全部 QA／补丁工具的确定性自测。

## 边界

- 引擎格式和二进制常量在绑定具体版本哈希前都只是候选。
- 静态体检与 QA 不能代替零变更回注和实际 UI、存读档、音频、回滚测试。
- 残留日文可能是有意保留项；应逐条审阅或维护明确排除表，不能静默放宽门禁。
- DeepSeek Harness 尚处于开发预览阶段，请固定到已审阅的插件版本。

贡献与安全报告方式见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [SECURITY.md](SECURITY.md)。

## 许可

[MIT](LICENSE)
