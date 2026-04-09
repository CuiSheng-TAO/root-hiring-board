// 自动生成 — 请勿手动编辑
// 更新时间: 2026.04.09 21:11
// 数据来源: 飞书电子表格 (一面/二面) + 招聘报告(入口) + 飞书 Hire API(ATS总数/候选人链接)
// ⚠️ 入口和笔试数据需要手动更新（见脚本顶部变量）

const DASHBOARD_DATA = {
  updateTime: "2026.04.09 21:11",
  dataPeriod: "0301 — till now",

  // 目标
  target: {
    goal: 10,
    current: 6,
    gap: 4
  },

  // 入口（⚠️ 需手动更新 — 来自飞书招聘报告页）
  entry: {
    resumesSent: 3003,
    assessPassed: 866,
    assessRate: 28
  },

  // 笔试（⚠️ 需手动更新 — 来自飞书 Wiki）
  writtenTest: {
    collected: 189,
    passed: 20,
    inProgress: 28,
    rejected: 28
  },

  // 一面（从电子表格自动计算）
  interview1: {
    current: {
      total: 14,
      passed: 6,
      rate: 42
    },
    bimonth: {
      total: 16,
      passed: 6,
      rate: 37
    }
  },

  // 二面（从电子表格自动计算）
  interview2: {
    current: {
      total: 6,
      passed: 2,
      pending: 4,
      rate: 33
    },
    bimonth: {
      total: 6,
      passed: 5,
      pending: 1,
      rate: 83
    }
  },

  // HR面（⚠️ 手动维护 — 候选人不常变动）
  hrInterview: {
    total: 4,
    candidates: [
      { name: "苗静思", status: "accept", label: "Offer 接受", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7605124900320495881", application_id: "7605124896885311771" },
      { name: "张杰", status: "accept", label: "Offer 沟通中", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7601899456342821129", application_id: "7621085664163563786" },
      { name: "阮傅浩", status: "reject", label: "无意向换工作", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7618999486904338697", application_id: "7618999656626489650" },
      { name: "魏弘量", status: "decline", label: "拒绝 Offer", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7615575380410386694", application_id: "7615617644800215346" }
    ]
  },

  // 链接
  links: {
    hireReport: "https://deepwisdom.feishu.cn/hire/reports/7578526668101258184",
    wiki: "https://deepwisdom.feishu.cn/wiki/Un5MwIF0oimoSukvwvjca9fznoN",
    interview1_12m: "https://deepwisdom.feishu.cn/sheets/HGh6splmdh8xgPtrDX1cNtT9ntb",
    interview1_3m: "https://deepwisdom.feishu.cn/sheets/XZUIsXtH5hgMoZt5IGZcv2hxnHh",
    interview2_detail: "https://deepwisdom.feishu.cn/sheets/HrIosFttQhvq3qt6iIPcIum5nNg",
    interview2_12m: "https://deepwisdom.feishu.cn/sheets/Wq33sHFBihdjm2tLRaCc9zHynR1"
  }
};
