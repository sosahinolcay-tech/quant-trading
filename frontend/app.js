const apiBaseInput = document.getElementById("apiBase");
const healthBtn = document.getElementById("healthCheck");
const healthStatus = document.getElementById("healthStatus");
const refreshAll = document.getElementById("refreshAll");

const runMarketMakerBtn = document.getElementById("runMarketMaker");
const runPairsBtn = document.getElementById("runPairs");
const runQualityBtn = document.getElementById("runQuality");
const runWalkForwardBtn = document.getElementById("runWalkForward");

const metricSharpe = document.getElementById("metricSharpe");
const metricHitRate = document.getElementById("metricHitRate");
const metricDrawdown = document.getElementById("metricDrawdown");
const metricGross = document.getElementById("metricGross");

const walkForwardTable = document.getElementById("walkForwardTable");
const qualityReport = document.getElementById("qualityReport");

const mmChartEl = document.getElementById("mmChart");
const pairsChartEl = document.getElementById("pairsChart");

let mmChart;
let pairsChart;

function baseUrl() {
  return apiBaseInput.value.replace(/\/+$/, "");
}

function globalParams() {
  return {
    interval: document.getElementById("globalInterval").value,
    start_date: document.getElementById("globalStart").value,
    end_date: document.getElementById("globalEnd").value,
  };
}

function setHealth(status, ok) {
  healthStatus.textContent = status;
  healthStatus.className = `status ${ok ? "ok" : "error"}`;
}

async function checkHealth() {
  try {
    const res = await fetch(`${baseUrl()}/health`);
    if (!res.ok) throw new Error("Health check failed");
    setHealth("Connected", true);
  } catch (err) {
    setHealth("Disconnected", false);
  }
}

function formatPct(value) {
  if (value === null || value === undefined) return "-";
  return `${(value * 100).toFixed(2)}%`;
}

function updateMetrics(summary) {
  metricSharpe.textContent = summary?.sharpe?.toFixed(2) ?? "-";
  metricHitRate.textContent = formatPct(summary?.hit_rate);
  metricDrawdown.textContent = formatPct(summary?.max_drawdown);
  metricGross.textContent = formatPct(summary?.avg_gross_exposure);
}

function buildChart(chartRef, canvas, label, data) {
  const labels = data.map((d) => new Date(d.timestamp * 1000).toLocaleTimeString());
  const values = data.map((d) => d.equity);
  if (chartRef) chartRef.destroy();
  return new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          borderColor: "#5ce1e6",
          backgroundColor: "rgba(92, 225, 230, 0.2)",
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { display: false }, y: { display: true } },
    },
  });
}

async function runMarketMaker() {
  const payload = {
    symbol: document.getElementById("mmSymbol").value,
    size: parseFloat(document.getElementById("mmSize").value),
    base_spread: parseFloat(document.getElementById("mmSpread").value),
    risk_aversion: parseFloat(document.getElementById("mmRisk").value),
    ...globalParams(),
  };
  const res = await fetch(`${baseUrl()}/run/market-maker`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Market maker run failed");
  const data = await res.json();
  updateMetrics(data.summary);
  if (data.equity?.length) {
    mmChart = buildChart(mmChart, mmChartEl, "Market Maker", data.equity);
  }
}

async function runPairs() {
  const payload = {
    symbol_x: document.getElementById("pairsX").value,
    symbol_y: document.getElementById("pairsY").value,
    entry_z: parseFloat(document.getElementById("pairsEntry").value),
    exit_z: parseFloat(document.getElementById("pairsExit").value),
    ...globalParams(),
  };
  const res = await fetch(`${baseUrl()}/run/pairs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Pairs run failed");
  const data = await res.json();
  updateMetrics(data.summary);
  if (data.equity?.length) {
    pairsChart = buildChart(pairsChart, pairsChartEl, "Pairs Strategy", data.equity);
  }
}

async function runQuality() {
  const payload = {
    symbol: document.getElementById("mmSymbol").value,
    ...globalParams(),
  };
  const res = await fetch(`${baseUrl()}/data/quality`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Quality check failed");
  const data = await res.json();
  if (!data.report) return;
  qualityReport.innerHTML = `
    <div>Rows: ${data.report.rows}</div>
    <div>Missing: ${formatPct(data.report.missing_pct)}</div>
    <div>Duplicates: ${formatPct(data.report.duplicate_pct)}</div>
    <div>Coverage: ${formatPct(data.report.coverage_pct)}</div>
    <div>Stale Seconds: ${data.report.stale_seconds.toFixed(0)}</div>
  `;
}

async function runWalkForward() {
  const payload = {
    symbol_x: document.getElementById("pairsX").value,
    symbol_y: document.getElementById("pairsY").value,
    interval: document.getElementById("globalInterval").value,
    range_str: "5d",
  };
  const res = await fetch(`${baseUrl()}/walk-forward`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Walk-forward failed");
  const data = await res.json();
  if (!data.results?.length) {
    walkForwardTable.textContent = "No walk-forward data.";
    return;
  }
  walkForwardTable.innerHTML = data.results
    .map(
      (row) =>
        `<div>Window ${row.window}: Sharpe ${row.sharpe.toFixed(2)}, Final ${row.final_equity.toFixed(2)}, Trades ${row.trades}</div>`
    )
    .join("");
}

healthBtn.addEventListener("click", checkHealth);
runMarketMakerBtn.addEventListener("click", runMarketMaker);
runPairsBtn.addEventListener("click", runPairs);
runQualityBtn.addEventListener("click", runQuality);
runWalkForwardBtn.addEventListener("click", runWalkForward);
refreshAll.addEventListener("click", async () => {
  await runMarketMaker();
  await runPairs();
  await runQuality();
});

checkHealth();
