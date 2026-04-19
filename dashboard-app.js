(function () {
  const appEl = document.getElementById("app");
  const CONFIG_URL = "./dashboard.config.json";

  let currentConfig = null;
  let currentData = null;

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function link(href, text, cls = "link") {
    return (
      '<a class="' +
      cls +
      '" href="' +
      href +
      '" target="_blank" rel="noopener">' +
      escapeHtml(text) +
      "</a>"
    );
  }

  function setLoading(message) {
    appEl.innerHTML =
      '<div class="loading-shell fade-in">' +
      '<div class="section-label">数据同步 <span class="tail">loading</span></div>' +
      '<div class="card loading-state">' +
      '<div class="loading-dot"></div>' +
      "<p>" +
      escapeHtml(message) +
      "</p>" +
      "</div>" +
      "</div>";
  }

  function setError(message) {
    appEl.innerHTML =
      '<div class="loading-shell fade-in">' +
      '<div class="section-label">数据同步 <span class="tail">error</span></div>' +
      '<div class="card error-state">' +
      "<p>" +
      escapeHtml(message) +
      "</p>" +
      '<button class="refresh-btn" id="retry-load">重新拉取数据</button>' +
      "</div>" +
      "</div>";

    const retryBtn = document.getElementById("retry-load");
    if (retryBtn) {
      retryBtn.addEventListener("click", function () {
        boot(true);
      });
    }
  }

  async function fetchJson(url, forceReload) {
    const finalUrl = forceReload
      ? url + (url.includes("?") ? "&" : "?") + "ts=" + Date.now()
      : url;
    const response = await fetch(finalUrl, {
      cache: forceReload ? "no-store" : "default",
    });
    if (!response.ok) {
      throw new Error("HTTP " + response.status + " for " + url);
    }
    return response.json();
  }

  async function loadConfig(forceReload) {
    return fetchJson(CONFIG_URL, forceReload);
  }

  async function loadData(config, forceReload) {
    const urls = (config.runtimeDataUrls || []).concat(["./data.json"]);
    let lastError = null;
    for (const url of urls) {
      try {
        return await fetchJson(url, forceReload);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError || new Error("No runtime data source worked.");
  }

  function renderScopeChips(data) {
    return (data.jobScope.matchedJobs || [])
      .map(function (job) {
        return (
          '<span class="scope-chip">' +
          escapeHtml(job.title) +
          '<span class="scope-chip-tail">' +
          escapeHtml(job.department || "未标注部门") +
          "</span>" +
          "</span>"
        );
      })
      .join("");
  }

  function renderInfoRows(config, data) {
    const rows = [
      ["操作时间", data.reportSource.operationWindow.start + " – " + data.reportSource.operationWindow.end],
      ["同步方式", data.runtime.autoSync],
      ["最近生成", data.generatedAt],
      ["权威报表", link(data.reportSource.widgetUrl, "飞书招聘报表")],
    ];

    return rows
      .map(function (row) {
        return (
          '<div class="info-row">' +
          '<span class="info-key">' +
          escapeHtml(row[0]) +
          "</span>" +
          '<span class="info-value">' +
          row[1] +
          "</span>" +
          "</div>"
        );
      })
      .join("");
  }

  function renderHeadcountNames(data) {
    const names = data.headcount && Array.isArray(data.headcount.matchedNames)
      ? data.headcount.matchedNames
      : [];

    if (!names.length) {
      return "";
    }

    return (
      '<div class="matched-line">' +
      '<span class="matched-label">当前在岗命中</span>' +
      '<div class="matched-names">' +
      names
        .map(function (name) {
          return '<span class="matched-name">' + escapeHtml(name) + "</span>";
        })
        .join("") +
      "</div>" +
      "</div>"
    );
  }

  function renderSummaryStages(data) {
    const stages = data.funnel.summaryStages || [];
    const maxCount = Math.max.apply(
      null,
      stages.map(function (stage) {
        return stage.count || 0;
      }).concat([1])
    );

    return stages
      .map(function (stage, index) {
        const previous = index > 0 ? stages[index - 1].count || 0 : 0;
        const rate = previous > 0 ? Math.round((stage.count / previous) * 100) : null;
        const width = Math.round((stage.count / maxCount) * 100);

        return (
          '<div class="funnel-step">' +
          '<div class="funnel-step-head">' +
          "<span>" +
          escapeHtml(stage.label) +
          "</span>" +
          '<span class="funnel-rate">' +
          (rate === null ? "—" : rate + "%") +
          "</span>" +
          "</div>" +
          '<div class="funnel-bar"><div class="funnel-bar-fill" style="width:' +
          width +
          '%"></div></div>' +
          '<div class="funnel-nums">' +
          (stage.count || 0).toLocaleString("zh-CN") +
          '<span class="unit">人次</span>' +
          "</div>" +
          "</div>"
        );
      })
      .join("");
  }

  function renderWeeklyTable(data) {
    const stageKeys = [
      "resume_screening",
      "resume_evaluation",
      "initial_invite",
      "interview_1",
      "interview_2",
      "hr_interview",
      "onboarded",
    ];
    const seriesMap = {};
    (data.funnel.weeklySeries || []).forEach(function (series) {
      seriesMap[series.key] = series;
    });

    const head = [
      "时间段",
      "简历初筛",
      "简历评估",
      "初面邀约",
      "专业一面",
      "专业二面",
      "HR面",
      "已入职",
    ];

    const rows = (data.funnel.weeklyLabels || []).map(function (label, index) {
      return (
        "<tr>" +
        "<td>" +
        escapeHtml(label) +
        "</td>" +
        stageKeys
          .map(function (key) {
            const count =
              seriesMap[key] && Array.isArray(seriesMap[key].counts)
                ? seriesMap[key].counts[index] || 0
                : 0;
            return "<td>" + count.toLocaleString("zh-CN") + "</td>";
          })
          .join("") +
        "</tr>"
      );
    });

    return (
      '<details class="card fold-card">' +
      '<summary class="fold-summary">' +
      '<div class="fold-copy">' +
      '<span class="fold-kicker">次级视图</span>' +
      '<span class="fold-title">阶段周趋势</span>' +
      '<span class="fold-desc">保留周度波动，但默认折叠，不抢主漏斗的注意力。</span>' +
      '</div>' +
      '<span class="fold-arrow">展开</span>' +
      "</summary>" +
      '<div class="weekly-card">' +
      '<table class="weekly-table">' +
      "<thead><tr>" +
      head
        .map(function (label) {
          return "<th>" + escapeHtml(label) + "</th>";
        })
        .join("") +
      "</tr></thead>" +
      "<tbody>" +
      rows.join("") +
      "</tbody>" +
      "</table>" +
      "</div>" +
      "</details>"
    );
  }

  function renderPipelineCandidates(data) {
    const sections = [];
    const stageMap = {
      interview_1: { label: "一面进行中", cls: "stage-i1" },
      interview_2: { label: "二面进行中", cls: "stage-i2" },
    };

    Object.keys(stageMap).forEach(function (key) {
      const items = data.pipelineCandidates[key] || [];
      if (!items.length) {
        return;
      }
      sections.push(
        '<div class="name-list-row">' +
          '<span class="name-list-section">' +
          stageMap[key].label +
          "</span> " +
          items
            .map(function (item) {
              return (
                '<a class="link name-tag ' +
                stageMap[key].cls +
                '" href="https://deepwisdom.feishu.cn/atsx/talent/' +
                encodeURIComponent(item.talent_id) +
                "?application_id=" +
                encodeURIComponent(item.application_id) +
                '" target="_blank" rel="noopener">' +
                escapeHtml(item.name) +
                "</a>"
              );
            })
            .join(" ") +
          "</div>"
      );
    });

    if (!sections.length) {
      return '<div class="card empty-state">当前没有正在进行中的一面 / 二面候选人。</div>';
    }

    return '<div class="card pipe-card"><div class="name-lists">' + sections.join("") + "</div></div>";
  }

  function candidateLink(candidate) {
    if (candidate.talent_id && candidate.application_id) {
      return link(
        "https://deepwisdom.feishu.cn/atsx/talent/" +
          encodeURIComponent(candidate.talent_id) +
          "?application_id=" +
          encodeURIComponent(candidate.application_id),
        candidate.name
      );
    }
    if (candidate.talent_id) {
      return link(
        "https://deepwisdom.feishu.cn/hire/talent/" + encodeURIComponent(candidate.talent_id),
        candidate.name
      );
    }
    return escapeHtml(candidate.name);
  }

  function renderHrCandidates(data) {
    const candidates = data.hrInterview.candidates || [];
    if (!candidates.length) {
      return '<div class="card empty-state">当前没有 HR 面出口候选人。</div>';
    }

    return (
      '<ul class="candidate-list">' +
      candidates
        .map(function (candidate) {
          const meta = [candidate.role, candidate.date].filter(Boolean).join(" · ");
          return (
            '<li class="candidate-card status-' +
            escapeHtml(candidate.status) +
            '">' +
            '<div class="candidate-avatar-inner">' +
            escapeHtml(candidate.name.slice(0, 1)) +
            "</div>" +
            '<div class="candidate-body">' +
            '<div class="candidate-name">' +
            candidateLink(candidate) +
            "</div>" +
            '<div class="candidate-meta">' +
            escapeHtml(meta) +
            "</div>" +
            "</div>" +
            '<span class="candidate-badge">' +
            escapeHtml(candidate.label) +
            "</span>" +
            "</li>"
          );
        })
        .join("") +
      "</ul>"
    );
  }

  function renderRefreshCard(data) {
    return (
      '<div class="info-list compact sync-list">' +
      '<div class="info-row"><span class="info-key">自动同步</span><span class="info-value">' +
      escapeHtml(data.runtime.autoSync) +
      "</span></div>" +
      '<div class="info-row"><span class="info-key">当前数据</span><span class="info-value">' +
      escapeHtml(data.generatedAt) +
      "</span></div>" +
      "</div>"
    );
  }

  function renderDashboard(config, data) {
    const target = data.target || { goal: 0, current: 0, gap: 0 };
    const progress = target.goal > 0 ? Math.min(Math.round((target.current / target.goal) * 100), 100) : 0;
    const firstStage = (data.funnel.summaryStages || [])[0]?.count || 0;
    const secondStage = (data.funnel.summaryStages || [])[1]?.count || 0;

    appEl.innerHTML =
      '<header class="header fade-in">' +
      '<div class="header-left">' +
      '<div class="eyebrow">Strategic Hire · Root Scope</div>' +
      "<h1>ROOT <em>全栈工程师</em> 招聘看板</h1>" +
      '<p class="hero-subtitle">把飞书招聘里的关键口径压成一页可读的战情摘要，让你一眼看见 HC 缺口、漏斗压力和出口状态。</p>' +
      "</div>" +
      '<div class="header-right">' +
      '<div class="live-badge">' +
      '<span class="live-dot"></span>' +
      "<span>自动同步 " +
      escapeHtml(data.runtime.autoSync) +
      "</span>" +
      "</div>" +
      "<span>更新 " +
      escapeHtml(data.generatedAt) +
      "</span>" +
      '<button class="refresh-btn" id="refresh-data">↻ 重新同步</button>' +
      '<button id="theme-toggle" class="theme-toggle"></button>' +
      "</div>" +
      "</header>" +
      '<main class="main">' +
      '<aside class="fade-in" style="animation-delay:0.06s;display:flex;flex-direction:column;gap:16px">' +
      '<div class="section-label">目标与范围 <span class="tail">objective</span></div>' +
      '<div class="metric-hero">' +
      '<div class="tag">HC GAP</div>' +
      '<div class="big-num">' +
      "<span>" +
      target.current +
      "</span>" +
      '<span class="sep">/</span>' +
      "<span>" +
      target.goal +
      "</span>" +
      '<span class="gap">−' +
      target.gap +
      "</span>" +
      "</div>" +
      '<div class="pct-line">' +
      target.current +
      " / " +
      target.goal +
      " 当前在岗 · " +
      progress +
      "%</div>" +
      '<div class="progress-bar"><div class="progress-fill" style="width:' +
      progress +
      '%"></div></div>' +
      "</div>" +
      '<div class="card info-card">' +
      '<div class="card-kicker">当前口径</div>' +
      '<div class="mini-note">ROOT 只按岗位白名单聚合。漏斗取飞书招聘权威报表，在岗人数取飞书通讯录命中名单。</div>' +
      '<div class="scope-chips">' +
      renderScopeChips(data) +
      "</div>" +
      '<div class="info-list">' +
      renderInfoRows(config, data) +
      "</div>" +
      renderHeadcountNames(data) +
      "</div>" +
      '<div class="card formula-card compact-formula">' +
      '<div class="card-kicker">快速参照</div>' +
      '<div class="formula-inline"><span>简历初筛 <strong>' +
      firstStage.toLocaleString("zh-CN") +
      '</strong></span><span>安排评估 <strong>' +
      secondStage.toLocaleString("zh-CN") +
      '</strong></span></div>' +
      '<div class="fc-proj">这里只留两项总量做左栏参照，详细阶段关系集中在中间主漏斗。</div>' +
      "</div>" +
      "</aside>" +
      '<section class="fade-in" style="animation-delay:0.1s;display:flex;flex-direction:column;gap:0">' +
      '<div class="section-label">权威漏斗 <span class="tail">' +
      escapeHtml(data.reportSource.operationWindow.start + " – " + data.reportSource.operationWindow.end) +
      "</span></div>" +
      '<div class="card" style="padding:0;overflow:hidden">' +
      '<div class="funnel-steps">' +
      renderSummaryStages(data) +
      "</div>" +
      "</div>" +
      renderWeeklyTable(data) +
      '<div class="section-label" style="margin-top:16px">当前候选人 <span class="tail">live pipeline</span></div>' +
      renderPipelineCandidates(data) +
      "</section>" +
      '<aside class="fade-in" style="animation-delay:0.14s;display:flex;flex-direction:column;gap:0">' +
      '<div class="section-label">HR 面 · 出口 <span class="tail">' +
      (data.hrInterview.total || 0) +
      " 人</span></div>" +
      renderHrCandidates(data) +
      '<div class="section-label" style="margin-top:16px">同步说明 <span class="tail">runtime</span></div>' +
      renderRefreshCard(data) +
      "</aside>" +
      "</main>";

    wireRefreshButton();
    wireThemeToggle();
  }

  function wireRefreshButton() {
    const button = document.getElementById("refresh-data");
    if (!button) return;
    button.addEventListener("click", async function () {
      button.disabled = true;
      button.textContent = "同步中...";
      try {
        await boot(true);
      } finally {
        button.disabled = false;
        button.textContent = "↻ 重新同步";
      }
    });
  }

  function wireThemeToggle() {
    const button = document.getElementById("theme-toggle");
    if (!button) return;

    function updateThemeButton() {
      const dark = document.documentElement.getAttribute("data-theme") === "dark";
      button.textContent = dark ? "☀" : "☾";
    }

    button.onclick = function () {
      const dark = document.documentElement.getAttribute("data-theme") === "dark";
      if (dark) {
        document.documentElement.removeAttribute("data-theme");
        localStorage.removeItem("theme");
      } else {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
      }
      updateThemeButton();
    };

    updateThemeButton();
  }

  async function boot(forceReload) {
    try {
      setLoading(forceReload ? "正在重新拉取最新数据..." : "正在读取招聘看板数据...");
      currentConfig = await loadConfig(forceReload);
      currentData = await loadData(currentConfig, forceReload);
      renderDashboard(currentConfig, currentData);
    } catch (error) {
      setError("招聘看板数据暂时不可用：" + error.message);
    }
  }

  boot(false);
})();
