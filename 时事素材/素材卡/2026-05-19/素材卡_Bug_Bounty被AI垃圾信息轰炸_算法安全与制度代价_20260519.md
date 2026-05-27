# 素材卡：Bug Bounty业务被AI垃圾信息轰炸——算法安全与制度代价

日期：2026-05-19
来源：https://arstechnica.com/ai/2026/05/bug-bounty-businesses-bombarded-with-ai-slop/
类型：算法主权/制度
可信度：secondary

## 一句话
AI工具大规模降低漏洞挖掘门槛，Bugcrowd等平台收到AI生成的垃圾报告数量在3周内翻两番；Curl、Nextcloud等暂停项目，AI安全产业格局面临重构。

## 关键事实
- Bugcrowd客户：OpenAI、T-Mobile、Motorola
- 报告增长：2026年3月某三周内，AI生成报告数量翻两番（>4倍）
- Curl暂停：2026年1月暂停付费bug bounty项目，因"AI垃圾报告爆炸"
- Nextcloud暂停：2026年4月因"低质量报告激增"暂停项目
- Bugcrowd报告：合法漏洞报告比例稳定在25%
- 第三方AI工具：Anthropic推出Mythos，可自动发现软件漏洞
- HackerOne：76%报告增长；引入"agentic validation capabilities"筛选AI报告

## 可用细节
- 垃圾报告制造者三类：
  1. 首次尝试的新手
  2. 被AI"引导"的现有研究人员
  3. 开发自动化扫描提交系统的"资深AI构建者"
- Daniel Stenberg（Curl作者）：AI垃圾报告"造成严重心理负担"
- Ross McKerchar（Sophos CISO）："bug bounty不会消失，但必须改变"
- 六位数漏洞奖金依然存在；Google 2022年最高单笔60.5万美元

## 小说映射
- 可映射章节/卷：第380章寒冰算力——算法安全与制度成本
- 对应变量：算法主权/算法暴力/制度
- 使用建议：可写"AI降低攻击门槛但也制造海量噪声"，安全研究员面临"信号vs噪音"的选择困境；制度层面可写"bug bounty平台作为安全公共品的局限性"

## 小黑盒选题
- 标题方向：《AI让所有人都能挖漏洞，但99%都是垃圾》
- 玩家切口："以后发现漏洞就像中彩票——但彩票站被机器人挤爆了"
- 可引用：HackerOne 76%增长、25%合法率

## 不可使用
- 不得将AI工具定性为"漏洞挖掘终结者"
- 不得忽略人类研究员的不可替代性
- 不得将暂停项目解读为"bug bounty已死"
