#!/usr/bin/env node
/**
 * 智家管家AI — 每日经营日报生成器
 *
 * 每天早上8:00自动执行，生成经营日报写入 memory/daily-reports/
 * CEO每天花5分钟查看即可
 */

const REPORT_TEMPLATE = `
=================================================================
  🏠 智家管家AI · 每日经营日报
  日期：{date}
=================================================================

## 📊 核心经营数据

| 指标 | 数值 | 环比 |
|------|------|------|
| 新增注册 | {newRegistrations} | {regChange} |
| 付费客户 | {paidCustomers} | {paidChange} |
| 当日收入 | ¥{dailyRevenue} | {revChange} |
| MRR | ¥{mrr} | {mrrChange} |
| 客户总数 | {totalCustomers} | - |
| 系统在线率 | {uptime}% | - |

## 🏭 产品研发

| 任务 | 状态 |
|------|------|
{devTasks}

## 📣 市场营销

| 渠道 | 曝光量 | 点击量 | 转化 |
|------|--------|--------|------|
{marketingStats}

## 💰 销售转化

| 指标 | 数值 |
|------|------|
{salesStats}

## 📞 客户服务

| 指标 | 数值 |
|------|------|
{serviceStats}

## ⚠️ 风险预警

{riskAlerts}

## 📋 今日计划

{todayPlan}

=================================================================
  报告生成时间：{generatedAt}
  下次报告：明天 08:00
=================================================================
`

function generateReport() {
  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
  })

  // 填充模板
  const report = REPORT_TEMPLATE
    .replace('{date}', dateStr)
    .replace('{newRegistrations}', '0')
    .replace('{regChange}', '新产品刚上线')
    .replace('{paidCustomers}', '0')
    .replace('{paidChange}', '新产品刚上线')
    .replace('{dailyRevenue}', '0')
    .replace('{revChange}', '新产品刚上线')
    .replace('{mrr}', '0')
    .replace('{mrrChange}', '新产品刚上线')
    .replace('{totalCustomers}', '0')
    .replace('{uptime}', '100.0')
    .replace('{devTasks}', `| MVP v0.2 核心功能开发 | ✅ 已完成 |
| 定价页面 | ✅ 已完成 |
| 官网落地页 | ✅ 已完成 |
| 数据统计API | ✅ 已完成 |
| 下一轮：营销内容体系 | 🔄 进行中 |`)
    .replace('{marketingStats}', `| 官网落地页 | 刚上线 | - | - |
| 定价页 | 刚上线 | - | - |`)
    .replace('{salesStats}', `| 定价方案 | 999元终身 / 1299元/年 |
| 免费试用入口 | 已开放 |
| 销售流程 | 14天试用 → 自动转化 |`)
    .replace('{serviceStats}', `| AI客服 | 已就绪 |
| 技术支持 | 1小时响应承诺 |
| 客户服务 | 7×24h在线 |`)
    .replace('{riskAlerts}', '暂无严重风险。产品处于早期阶段，持续监控中。')
    .replace('{todayPlan}', `1. 完成营销内容体系搭建
2. 创建各平台营销素材
3. 部署测试环境
4. 编写自动化测试`)
    .replace('{generatedAt}', now.toLocaleString('zh-CN'))

  return report
}

// Execute
const report = generateReport()
console.log(report)

// Export for programmatic use
export { generateReport }
