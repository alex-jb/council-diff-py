# council-diff-py

> [council-diff](https://github.com/alex-jb/council-diff) 的 Python 移植——5 voice AI 议会决策。
> [English](README.md) · [中文](README.zh-CN.md)

TypeScript [`council-diff`](https://github.com/alex-jb/council-diff) 的 Python 移植版本。同样的架构,同 6 个内置 domain,同 Brier 审核数学。

## 安装

```bash
pip install council-diff
```

## 快速开始

```python
from council_diff import CouncilDiff

council = CouncilDiff(api_key=None)  # 没传时从 ANTHROPIC_API_KEY 读

result = council.deliberate(
    domain="founder",
    decision="我应该 raise $1M 种子轮还是 bootstrap?",
    context="B2B SaaS, $5K MRR, 月增 20%, solo 创业, 12mo runway",
)

print(result.recommendation)       # "go" | "wait" | "kill" | "split"
print(result.agreement_score)      # 0-1
print(result.consensus)            # 1 段综合

for v in result.voices:
    print(f"{v.voice_display} ({v.score}/100): {v.verdict}")
    print(f"  + {v.strength}")
    print(f"  - {v.gap}")
```

## Brier 审核

```python
from council_diff.brier import add_prediction, resolve_prediction, brier_score, mean_brier

pred = add_prediction(
    decision=result.decision,
    domain=result.domain,
    recommendation=result.recommendation,
    agreement_score=result.agreement_score,
    voice_scores=[v.score for v in result.voices],
    resolve_by="2027-06-09",
)

# 12mo 后结果出来:
resolved = resolve_prediction(pred, outcome="go-was-right")
score = brier_score(resolved)  # 0=完美, 1=最差, 0.25=随机

# 多个聚合:
audit = mean_brier(all_resolved_preds)
print(audit["edge_vs_random"])  # 正数 = council 比随机有 calibration 价值
```

## 路线图

- [x] 脚手架 + TypeScript 版同步 spec
- [ ] `pip install council-diff` 发布
- [ ] CLI: `council "我该不该辞职" --domain career`
- [ ] FastAPI server 自托管

## 许可

MIT
