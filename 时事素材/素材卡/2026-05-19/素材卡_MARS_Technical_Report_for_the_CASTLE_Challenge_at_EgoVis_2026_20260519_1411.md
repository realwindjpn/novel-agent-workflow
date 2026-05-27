# 素材卡：MARS: Technical Report for the CASTLE Challenge at EgoVis 2026

日期：2026-05-19
来源：https://arxiv.org/abs/2605.18176
来源域名：arxiv.org
类型：深空工程
可信度：secondary
原文状态：OK
候选来源：opencli_arxiv_20260519

## 一句话
opencli结构化检索：月球/深空工程 / arxiv / deep space communication delay Mars operations NASA 2026

## 关键事实
- We gratefully acknowledge support from the Simons Foundation, member institutions , and all contributors.
- Participants must answer 185 closed-form questions over the CASTLE 2024 dataset.
- MARS therefore treats the task as an agentic evidence-selection problem over multimodal sources rather than a purely text-only pipeline.
- The resulting system achieved second place on the final CASTLE Challenge leaderboard.

## 可用细节
- 月球：可转成角色看到的表格、告警、回执、库存或倒计时。

## 小说映射
- 可映射章节/卷：待主控按大纲缺口分配。
- 对应变量：深空工程 / 供应链 / 制度摩擦 / 技术边界。
- 使用建议：只作素材候选；进入正文前需角色任务卡二次筛选。

## 小黑盒选题
- 标题方向：MARS: Technical Report for the CASTLE Challenge at EgoVis 2026背后的现实成本。
- 玩家/普通人口吻切口：不是概念，落到谁付钱、谁等审批、谁被系统卡住。

## 不可使用
- 原文状态为 MISSING_RAW 时，不得当作 primary fact。
- 不把评论/候选摘要当事实。
- 不直接改大纲或正文。

## 原文摘录 / 抽取日志
[2605.18176] MARS: Technical Report for the CASTLE Challenge at EgoVis 2026 Skip to main content Learn about arXiv becoming an independent nonprofit. We gratefully acknowledge support from the Simons Foundation, member institutions , and all contributors. Donate &gt; cs &gt; arXiv:2605.18176 Help | Advanced Search All fields Title Author Abstract Comments Journal reference ACM classification MSC classification Report number arXiv identifier DOI ORCID arXiv author ID Help pages Full text Search GO quick links Login Help Pages About --> Computer Science > Computer Vision and Pattern Recognition arXiv:2605.18176 (cs) [Submitted on 18 May 2026] Title: MARS: Technical Report for the CASTLE Challenge at EgoVis 2026 Authors: Haoyu Zhang , Qiaohui Chu , Yisen Feng , Meng Liu , Weili Guan , Yaowei Wang , Liqiang Nie View a PDF of the paper titled MARS: Technical Report for the CASTLE Challenge at EgoVis 2026, by Haoyu Zhang and 6 other authors View PDF HTML (experimental) Abstract: This report presents MARS, short for Multimodal Agentic Reasoning with Source selection, our system for the CASTLE Challenge at EgoVis 2026. Participants must answer 185 closed-form questions over the CASTLE 2024 dataset. In contrast to prior single-video egocentric benchmarks, CASTLE requires reasoning over four days of activity, 15 synchronized perspectives, official transcripts, and multiple auxiliary modalities, including personal photos, auxiliary videos, gaze, thermal imagery, and heartrate measurements. MARS therefore treats the task as an agentic evidence-selection problem over multimodal sources rather than a purely text-only pipeline. MARS first follows the official CASTLE directory organization to build evidence memories from two primary sources, videos and transcripts, and four auxiliary sources, gaze, heartrate, photos, and thermal imagery. Long videos are converted into captions and DeepSeek-based summaries only because CASTLE videos are too long to fit directly into the model context for every question; this step compresses temporal evidence while keeping photos and other auxiliary media available as source-specific evidence. At inference time, a GPT-5.4 decision agent repeatedl
