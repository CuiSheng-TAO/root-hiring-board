(function () {
  const appEl = document.getElementById("app");
  const CONFIG_URL = "./dashboard.config.json";

  let currentConfig = null;
  let currentData = null;
  let calStart = null;
  let calEnd = null;
  let calYear = new Date().getFullYear();
  let calMonth = new Date().getMonth();
  let calPicking = 0;
  let hasCustomRange = false;
  let outsideClickHandler = null;

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

  function pad2(value) {
    return String(value).padStart(2, "0");
  }

  function parseIsoDate(value) {
    return value ? new Date(value + "T00:00:00") : null;
  }

  function fmtIso(value) {
    return (
      value.getFullYear() +
      "-" +
      pad2(value.getMonth() + 1) +
      "-" +
      pad2(value.getDate())
    );
  }

  function sameDay(a, b) {
    return !!(a && b && fmtIso(a) === fmtIso(b));
  }

  function getDefaultRange(data) {
    return {
      start: parseIsoDate(data.reportSource.operationWindow.start),
      end: parseIsoDate(data.reportSource.operationWindow.end),
    };
  }

  function buildWeekRanges(startIso, endIso) {
    const ranges = [];
    let cursor = parseIsoDate(startIso);
    const end = parseIsoDate(endIso);
    while (cursor && end && cursor <= end) {
      const segmentStart = new Date(cursor);
      const day = cursor.getDay() || 7;
      const segmentEnd = new Date(cursor);
      segmentEnd.setDate(segmentEnd.getDate() + (7 - day));
      if (segmentEnd > end) segmentEnd.setTime(end.getTime());
      ranges.push({
        start: fmtIso(segmentStart),
        end: fmtIso(segmentEnd),
        label:
          pad2(segmentStart.getMonth() + 1) +
          "-" +
          pad2(segmentStart.getDate()) +
          " – " +
          pad2(segmentEnd.getMonth() + 1) +
          "-" +
          pad2(segmentEnd.getDate()),
      });
      cursor = new Date(segmentEnd);
      cursor.setDate(cursor.getDate() + 1);
    }
    return ranges;
  }

  function getWeekRanges(data) {
    if (Array.isArray(data.funnel.weeklyRanges) && data.funnel.weeklyRanges.length) {
      return data.funnel.weeklyRanges;
    }
    return buildWeekRanges(
      data.reportSource.operationWindow.start,
      data.reportSource.operationWindow.end
    );
  }

  function formatRangeButton(start, end, data) {
    const defaults = getDefaultRange(data);
    const left = start || defaults.start;
    const right = end || defaults.end;
    return fmtIso(left) + '<span class="sep">至</span>' + fmtIso(right);
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
      '<div class="card loading-state">' +
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

  function renderInfoRows(data) {
    return [
      ["操作时间", data.reportSource.operationWindow.start + " – " + data.reportSource.operationWindow.end],
      ["同步方式", data.runtime.autoSync],
      ["最近生成", data.generatedAt],
      ["权威报表", link(data.reportSource.widgetUrl, "飞书招聘报表")],
    ]
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
    const names =
      data.headcount && Array.isArray(data.headcount.matchedNames)
        ? data.headcount.matchedNames
        : [];
    if (!names.length) return "";
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

  function candidateDate(item) {
    if (item.dateIso) return parseIsoDate(item.dateIso);
    if (item.date) {
      const year = currentData
        ? currentData.reportSource.operationWindow.start.slice(0, 4)
        : String(new Date().getFullYear());
      return parseIsoDate(year + "-" + item.date);
    }
    return null;
  }

  function filterCandidateSet(items, start, end) {
    if (!hasCustomRange || !start || !end) return items || [];
    return (items || []).filter(function (item) {
      const date = candidateDate(item);
      return !date || (date >= start && date <= end);
    });
  }

  function buildDateSet(data) {
    const set = {};
    const defaults = getDefaultRange(data);
    const cursor = new Date(defaults.start);
    while (cursor <= defaults.end) {
      set[fmtIso(cursor)] = true;
      cursor.setDate(cursor.getDate() + 1);
    }
    const daily = data.funnel.dailyStageEntries || {};
    Object.keys(daily).forEach(function (key) {
      set[key] = true;
    });
    ["interview_1", "interview_2"].forEach(function (key) {
      (data.pipelineCandidates[key] || []).forEach(function (item) {
        const date = candidateDate(item);
        if (date) set[fmtIso(date)] = true;
      });
    });
    (data.hrInterview.candidates || []).forEach(function (item) {
      const date = candidateDate(item);
      if (date) set[fmtIso(date)] = true;
    });
    return set;
  }

  function aggregateStageCounts(data, start, end) {
    if (!hasCustomRange || !start || !end) {
      return data.funnel.summaryStages || [];
    }
    const counts = {
      resume_screening: 0,
      resume_evaluation: 0,
      initial_invite: 0,
      interview_1: 0,
      interview_2: 0,
      hr_interview: 0,
      onboarded: 0,
    };
    const daily = data.funnel.dailyStageEntries || {};
    const hasDaily = Object.keys(daily).length > 0;

    if (hasDaily) {
      Object.keys(daily).forEach(function (key) {
        const date = parseIsoDate(key);
        if (!date || date < start || date > end) return;
        const row = daily[key];
        Object.keys(counts).forEach(function (stageKey) {
          counts[stageKey] += row[stageKey] || 0;
        });
      });
    } else {
      const weekRanges = getWeekRanges(data);
      const weekly = {};
      (data.funnel.weeklySeries || []).forEach(function (series) {
        weekly[series.key] = series.counts || [];
      });
      weekRanges.forEach(function (range, index) {
        const rangeStart = parseIsoDate(range.start);
        const rangeEnd = parseIsoDate(range.end);
        if (!rangeStart || !rangeEnd || rangeEnd < start || rangeStart > end) return;
        Object.keys(counts).forEach(function (stageKey) {
          counts[stageKey] += weekly[stageKey] ? weekly[stageKey][index] || 0 : 0;
        });
      });
    }

    const summaryMap = {};
    (data.funnel.summaryStages || []).forEach(function (stage) {
      summaryMap[stage.key] = stage.label;
    });
    return [
      ["resume_screening", counts.resume_screening],
      ["assigned_evaluation", counts.resume_evaluation],
      ["initial_invite", counts.initial_invite],
      ["interview_1", counts.interview_1],
      ["conduct_interview_1", counts.interview_1],
      ["interview_2", counts.interview_2],
      ["hr_interview", counts.hr_interview],
      ["onboarded", counts.onboarded],
    ].map(function (entry) {
      return {
        key: entry[0],
        label: summaryMap[entry[0]] || entry[0],
        count: entry[1],
      };
    });
  }

  function filterWeeklySeries(data, start, end) {
    const weekRanges = getWeekRanges(data);
    const labels = data.funnel.weeklyLabels || weekRanges.map(function (item) { return item.label; });
    if (!hasCustomRange || !start || !end) {
      return { labels: labels, series: data.funnel.weeklySeries || [] };
    }
    const indexes = weekRanges
      .map(function (range, index) {
        const rangeStart = parseIsoDate(range.start);
        const rangeEnd = parseIsoDate(range.end);
        if (!rangeStart || !rangeEnd || rangeEnd < start || rangeStart > end) return null;
        return index;
      })
      .filter(function (value) { return value !== null; });

    return {
      labels: indexes.map(function (index) { return labels[index]; }),
      series: (data.funnel.weeklySeries || []).map(function (series) {
        return {
          key: series.key,
          label: series.label,
          counts: indexes.map(function (index) {
            return (series.counts || [])[index] || 0;
          }),
        };
      }),
    };
  }

  function renderSummaryStages(stages) {
    const maxCount = Math.max.apply(
      null,
      (stages || [])
        .map(function (stage) { return stage.count || 0; })
        .concat([1])
    );

    return (stages || [])
      .map(function (stage, index) {
        const previous = index > 0 ? (stages[index - 1].count || 0) : 0;
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

  function renderWeeklyTable(labels, series) {
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
    (series || []).forEach(function (item) {
      seriesMap[item.key] = item;
    });

    const rows = (labels || []).map(function (label, index) {
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
      '<details class="fold-card">' +
      '<summary class="fold-summary">' +
      '<div class="fold-copy">' +
      '<span class="fold-kicker">次级视图</span>' +
      '<span class="fold-title">阶段周趋势</span>' +
      '<span class="fold-desc">你可以保留主漏斗不变，同时按选中时间段查看趋势分布。</span>' +
      "</div>" +
      '<span class="fold-arrow">展开</span>' +
      "</summary>" +
      '<div class="weekly-card">' +
      '<table class="weekly-table">' +
      "<thead><tr><th>时间段</th><th>简历初筛</th><th>简历评估</th><th>初面邀约</th><th>专业一面</th><th>专业二面</th><th>HR面</th><th>已入职</th></tr></thead>" +
      "<tbody>" +
      rows.join("") +
      "</tbody></table></div></details>"
    );
  }

  function renderPipelineCandidates(data, start, end) {
    const sections = [];
    const stageMap = {
      interview_1: { label: "一面进行中", cls: "stage-i1" },
      interview_2: { label: "二面进行中", cls: "stage-i2" },
    };

    Object.keys(stageMap).forEach(function (key) {
      const items = filterCandidateSet(data.pipelineCandidates[key] || [], start, end);
      if (!items.length) return;
      sections.push(
        '<div class="name-list-row">' +
        '<span class="name-list-section">' + stageMap[key].label + "</span> " +
        items
          .map(function (item) {
            return (
              '<a class="link name-tag ' + stageMap[key].cls +
              '" href="https://deepwisdom.feishu.cn/atsx/talent/' +
              encodeURIComponent(item.talent_id) +
              "?application_id=" + encodeURIComponent(item.application_id) +
              '" target="_blank" rel="noopener">' +
              escapeHtml(item.name) + "</a>"
            );
          })
          .join(" ") +
        "</div>"
      );
    });

    if (!sections.length) {
      return '<div class="card empty-state">当前时间范围内没有正在进行中的一面 / 二面候选人。</div>';
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

  function renderHrCandidates(data, start, end) {
    const candidates = filterCandidateSet(data.hrInterview.candidates || [], start, end);
    if (!candidates.length) {
      return {
        html: '<div class="card empty-state">当前时间范围内没有 HR 面出口候选人。</div>',
        total: 0,
      };
    }

    return {
      total: candidates.length,
      html:
        '<ul class="candidate-list">' +
        candidates
          .map(function (candidate) {
            const meta = [candidate.role, candidate.date].filter(Boolean).join(" · ");
            return (
              '<li class="candidate-card status-' + escapeHtml(candidate.status) + '">' +
              '<div class="candidate-avatar-inner">' + escapeHtml(candidate.name.slice(0, 1)) + "</div>" +
              '<div class="candidate-body">' +
              '<div class="candidate-name">' + candidateLink(candidate) + "</div>" +
              '<div class="candidate-meta">' + escapeHtml(meta) + "</div>" +
              "</div>" +
              '<span class="candidate-badge">' + escapeHtml(candidate.label) + "</span>" +
              "</li>"
            );
          })
          .join("") +
        "</ul>",
    };
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

  function renderCalendar(dataDates) {
    const grid = document.getElementById("cal-grid");
    const title = document.getElementById("cal-title");
    if (!grid || !title) return;
    title.textContent = calYear + "年" + (calMonth + 1) + "月";

    const first = new Date(calYear, calMonth, 1);
    const dow = (first.getDay() + 6) % 7;
    const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
    const prevDays = new Date(calYear, calMonth, 0).getDate();
    const today = new Date();
    const todayKey = fmtIso(today);
    let html = "";

    for (let p = dow - 1; p >= 0; p--) {
      const day = prevDays - p;
      let month = calMonth - 1;
      let year = calYear;
      if (month < 0) {
        month = 11;
        year -= 1;
      }
      const key = year + "-" + pad2(month + 1) + "-" + pad2(day);
      html += '<div class="cal-day other-month' + (dataDates[key] ? " has-data" : "") + '">' + day + "</div>";
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const key = calYear + "-" + pad2(calMonth + 1) + "-" + pad2(day);
      const date = parseIsoDate(key);
      let cls = "cal-day";
      if (key === todayKey) cls += " today";
      if (dataDates[key]) cls += " has-data";
      if (calStart && calEnd && date) {
        if (sameDay(date, calStart) || sameDay(date, calEnd)) cls += " selected";
        else if (date > calStart && date < calEnd) cls += " in-range";
      } else if (calStart && date && sameDay(date, calStart)) {
        cls += " selected";
      }
      html += '<div class="' + cls + '" data-date="' + key + '">' + day + "</div>";
    }

    const totalCells = dow + daysInMonth;
    const remaining = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    for (let day = 1; day <= remaining; day++) {
      let month = calMonth + 1;
      let year = calYear;
      if (month > 11) {
        month = 0;
        year += 1;
      }
      const key = year + "-" + pad2(month + 1) + "-" + pad2(day);
      html += '<div class="cal-day other-month' + (dataDates[key] ? " has-data" : "") + '">' + day + "</div>";
    }
    grid.innerHTML = html;
  }

  function wireDateFilter(data, dataDates, defaultRange) {
    const rangeDisplayBtn = document.getElementById("range-display");
    const presetBtn = document.getElementById("preset-all");
    const dropdown = document.getElementById("cal-dropdown");
    if (!rangeDisplayBtn || !presetBtn || !dropdown) return;

    function openCalendar() {
      dropdown.style.display = "block";
      renderCalendar(dataDates);
    }

    function closeCalendar() {
      dropdown.style.display = "none";
    }

    rangeDisplayBtn.onclick = function (event) {
      event.stopPropagation();
      if (dropdown.style.display === "none") openCalendar();
      else closeCalendar();
    };

    presetBtn.onclick = function (event) {
      event.stopPropagation();
      hasCustomRange = false;
      calStart = defaultRange.start;
      calEnd = defaultRange.end;
      calPicking = 0;
      renderDashboard(currentConfig, currentData);
    };

    document.getElementById("cal-prev").onclick = function (event) {
      event.stopPropagation();
      calMonth -= 1;
      if (calMonth < 0) {
        calMonth = 11;
        calYear -= 1;
      }
      renderCalendar(dataDates);
    };

    document.getElementById("cal-next").onclick = function (event) {
      event.stopPropagation();
      calMonth += 1;
      if (calMonth > 11) {
        calMonth = 0;
        calYear += 1;
      }
      renderCalendar(dataDates);
    };

    document.getElementById("cal-grid").onclick = function (event) {
      event.stopPropagation();
      const cell = event.target.closest(".cal-day");
      if (!cell) return;
      const value = cell.getAttribute("data-date");
      if (!value) return;
      const picked = parseIsoDate(value);
      if (!picked) return;
      if (calPicking === 0) {
        calStart = picked;
        calEnd = null;
        calPicking = 1;
        renderCalendar(dataDates);
      } else {
        calEnd = picked;
        if (calEnd < calStart) {
          const temp = calStart;
          calStart = calEnd;
          calEnd = temp;
        }
        hasCustomRange = true;
        calPicking = 0;
        closeCalendar();
        renderDashboard(currentConfig, currentData);
      }
    };

    document.getElementById("cal-all").onclick = function (event) {
      event.stopPropagation();
      hasCustomRange = false;
      calStart = defaultRange.start;
      calEnd = defaultRange.end;
      calPicking = 0;
      closeCalendar();
      renderDashboard(currentConfig, currentData);
    };

    if (outsideClickHandler) {
      document.removeEventListener("click", outsideClickHandler);
    }
    outsideClickHandler = function (event) {
      if (!dropdown.contains(event.target) && event.target !== rangeDisplayBtn) {
        closeCalendar();
      }
    };
    document.addEventListener("click", outsideClickHandler);
  }

  function renderDashboard(config, data) {
    const defaultRange = getDefaultRange(data);
    const summaryStages = aggregateStageCounts(data, calStart, calEnd);
    const weeklyView = filterWeeklySeries(data, calStart, calEnd);
    const hrView = renderHrCandidates(data, calStart, calEnd);
    const rangeTail = hasCustomRange && calStart && calEnd
      ? fmtIso(calStart) + " – " + fmtIso(calEnd)
      : data.reportSource.operationWindow.start + " – " + data.reportSource.operationWindow.end;
    const target = data.target || { goal: 0, current: 0, gap: 0 };
    const progress = target.goal > 0 ? Math.min(Math.round((target.current / target.goal) * 100), 100) : 0;
    const firstStage = (summaryStages || [])[0]?.count || 0;
    const secondStage = (summaryStages || [])[1]?.count || 0;

    appEl.innerHTML =
      '<header class="header fade-in">' +
      '<div class="header-left">' +
      '<div class="eyebrow">Strategic Hire · Root Scope</div>' +
      "<h1>ROOT <em>全栈工程师</em> 招聘看板</h1>" +
      '<p class="hero-subtitle">把飞书招聘里的关键口径压成一页可读的战情摘要，让你一眼看见 HC 缺口、漏斗压力和出口状态。</p>' +
      "</div>" +
      '<div class="header-right">' +
      '<div class="date-filter-group">' +
      '<button class="preset-btn' + (!hasCustomRange ? " active" : "") + '" id="preset-all">权威窗口</button>' +
      '<button class="range-display' + (hasCustomRange ? " active" : "") + '" id="range-display">' +
      formatRangeButton(calStart, calEnd, data) +
      "</button>" +
      '<div class="cal-dropdown" id="cal-dropdown" style="display:none">' +
      '<div class="cal-header"><button class="cal-nav" id="cal-prev">‹</button><span id="cal-title"></span><button class="cal-nav" id="cal-next">›</button></div>' +
      '<div class="cal-weekdays"><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span></div>' +
      '<div class="cal-grid" id="cal-grid"></div>' +
      '<div class="cal-actions"><button class="cal-btn" id="cal-all">重置</button></div>' +
      "</div></div>" +
      '<div class="live-badge"><span class="live-dot"></span><span>自动同步 ' + escapeHtml(data.runtime.autoSync) + "</span></div>" +
      "<span>更新 " + escapeHtml(data.generatedAt) + "</span>" +
      '<button class="refresh-btn" id="refresh-data">↻ 重新同步</button>' +
      '<button id="theme-toggle" class="theme-toggle"></button>' +
      "</div></header>" +
      '<main class="main">' +
      '<aside class="fade-in" style="animation-delay:0.06s;display:flex;flex-direction:column;gap:16px">' +
      '<div class="section-label">目标与范围 <span class="tail">objective</span></div>' +
      '<div class="metric-hero"><div class="tag">HC GAP</div><div class="big-num"><span>' +
      target.current +
      '</span><span class="sep">/</span><span>' +
      target.goal +
      '</span><span class="gap">−' +
      target.gap +
      '</span></div><div class="pct-line">' +
      target.current +
      " / " +
      target.goal +
      " 当前在岗 · " +
      progress +
      '%</div><div class="progress-bar"><div class="progress-fill" style="width:' +
      progress +
      '%"></div></div></div>' +
      '<div class="card info-card"><div class="card-kicker">当前口径</div><div class="mini-note">ROOT 只按岗位白名单聚合。漏斗取飞书招聘权威报表，在岗人数取飞书通讯录命中名单。</div><div class="scope-chips">' +
      renderScopeChips(data) +
      '</div><div class="info-list">' +
      renderInfoRows(data) +
      "</div>" +
      renderHeadcountNames(data) +
      "</div>" +
      '<div class="card formula-card compact-formula"><div class="card-kicker">快速参照</div><div class="formula-inline"><span>简历初筛 <strong>' +
      firstStage.toLocaleString("zh-CN") +
      '</strong></span><span>安排评估 <strong>' +
      secondStage.toLocaleString("zh-CN") +
      '</strong></span></div><div class="fc-proj">这里只留两项总量做左栏参照，详细阶段关系集中在中间主漏斗。</div></div>' +
      "</aside>" +
      '<section class="fade-in" style="animation-delay:0.1s;display:flex;flex-direction:column;gap:0">' +
      '<div class="section-label">权威漏斗 <span class="tail">' + escapeHtml(rangeTail) + "</span></div>" +
      '<div class="card" style="padding:0;overflow:hidden"><div class="funnel-steps">' +
      renderSummaryStages(summaryStages) +
      "</div></div>" +
      renderWeeklyTable(weeklyView.labels, weeklyView.series) +
      '<div class="section-label" style="margin-top:16px">当前候选人 <span class="tail">live pipeline</span></div>' +
      renderPipelineCandidates(data, calStart, calEnd) +
      "</section>" +
      '<aside class="fade-in" style="animation-delay:0.14s;display:flex;flex-direction:column;gap:0">' +
      '<div class="section-label">HR 面 · 出口 <span class="tail">' + hrView.total + " 人</span></div>" +
      hrView.html +
      '<div class="section-label" style="margin-top:16px">同步说明 <span class="tail">runtime</span></div>' +
      renderRefreshCard(data) +
      "</aside></main>";

    wireRefreshButton();
    wireThemeToggle();
    wireDateFilter(data, buildDateSet(data), defaultRange);
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
      const defaults = getDefaultRange(currentData);
      calStart = defaults.start;
      calEnd = defaults.end;
      calYear = calStart.getFullYear();
      calMonth = calStart.getMonth();
      calPicking = 0;
      renderDashboard(currentConfig, currentData);
    } catch (error) {
      setError("招聘看板数据暂时不可用：" + error.message);
    }
  }

  boot(false);
})();
