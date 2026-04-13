// 自动生成 — 请勿手动编辑
// 更新时间: 2026.04.10 11:08
// 数据来源: 飞书电子表格 (一面/二面) + 招聘报告(入口) + 飞书 Hire API(ATS总数/候选人链接)
// ⚠️ 入口和笔试数据需要手动更新（见脚本顶部变量）

const DASHBOARD_DATA = {
  updateTime: "2026.04.10 11:08",
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
    },
    candidates: [{"talent_id": "7618445027626207494", "application_id": "7621408582815222058", "name": "李镇杞"}, {"talent_id": "7618484688591587593", "application_id": "7618484626588403978", "name": "陈宇杰"}, {"talent_id": "7618999486904338697", "application_id": "7618999656626489650", "name": "阮傅浩"}, {"talent_id": "7605124900320495881", "application_id": "7621075682273184046", "name": "苗静思"}, {"talent_id": "7601899456342821129", "application_id": "7621085664163563786", "name": "张杰"}, {"talent_id": "7600956211659622675", "application_id": "7600956305419290922", "name": "梁栩才"}, {"talent_id": "7620662710405171502", "application_id": "7620662689790003466", "name": "何伟杰"}, {"talent_id": "7603218770996807962", "application_id": "7603218947648178478", "name": "温正畅"}, {"talent_id": "7620719893336115510", "application_id": "7620719865960581382", "name": "梅嘉玉"}, {"talent_id": "7618429536838273318", "application_id": "7618429611600840986", "name": "刘嘉慧"}, {"talent_id": "7619794889514240319", "application_id": "7619790588137916715", "name": "田毅"}, {"talent_id": "7613275799731112255", "application_id": "7613275789589547318", "name": "李承熙"}, {"talent_id": "7612540687938357523", "application_id": "7612540700698118442", "name": "黄国全"}, {"talent_id": "7610645088984664339", "application_id": "7610645095322569002", "name": "李华浩"}],
    candidates12m: [{"name": "欧聪杰"}, {"name": "方晓生"}, {"name": "汤龙鑫"}, {"name": "梅嘉玉"}, {"name": "何伟杰"}, {"name": "刘嘉慧"}, {"name": "李镇杞"}, {"name": "田毅"}, {"name": "陈宇杰"}, {"name": "阮傅浩"}, {"name": "李承熙"}, {"name": "黄国全"}, {"name": "苗静思"}, {"name": "张杰"}, {"name": "温正畅"}, {"name": "李华浩"}, {"name": "梁栩才"}]
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
    },
    candidates: [{"talent_id": "7605124900320495881", "application_id": "7621075682273184046", "name": "苗静思"}, {"talent_id": "7618999486904338697", "application_id": "7618999656626489650", "name": "阮傅浩"}, {"talent_id": "7618445027626207494", "application_id": "7621408582815222058", "name": "李镇杞"}, {"talent_id": "7618484688591587593", "application_id": "7618484626588403978", "name": "陈宇杰"}, {"talent_id": "7615575380410386694", "application_id": "7615617644800215346", "name": "魏弘量"}, {"talent_id": "7601899456342821129", "application_id": "7621085664163563786", "name": "张杰"}],
    candidates12m: [{"talent_id": "7597747641795856646", "application_id": "7597747675622639926", "name": "苏文昊"}, {"talent_id": "7596906017489996038", "application_id": "7596905995000449343", "name": "张雪洋"}, {"talent_id": "7596910286994311467", "application_id": "7597050550866430234", "name": "Li Ruibin"}, {"talent_id": "7584682092735645971", "application_id": "7584681754524518719", "name": "张星宇"}, {"talent_id": "7595548076820400420", "application_id": "7595548343728818473", "name": "Lifei Chen"}, {"talent_id": "7582505643124738346", "application_id": "7597388348587985188", "name": "史斌"}]
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
    interview1_3m: "https://deepwisdom.feishu.cn/hire/reports/762705618927226317/widgets/7627056189327576021",
    interview2_detail: "https://deepwisdom.feishu.cn/sheets/HrIosFttQhvq3qt6iIPcIum5nNg",
    interview2_12m: "https://deepwisdom.feishu.cn/sheets/Wq33sHFBihdjm2tLRaCc9zHynR1"
  }
};
