const apiBaseInput = document.getElementById("apiBase");
const healthBtn = document.getElementById("healthCheck");
const healthStatus = document.getElementById("healthStatus");
const refreshAll = document.getElementById("refreshAll");

const runMarketMakerBtn = document.getElementById("runMarketMaker");
const runPairsBtn = document.getElementById("runPairs");
const runQualityBtn = document.getElementById("runQuality");
const runWalkForwardBtn = document.getElementById("runWalkForward");
const runDataExplorerBtn = document.getElementById("runDataExplorer");
const refreshProvidersBtn = document.getElementById("refreshProviders");
const downloadDataBtn = document.getElementById("downloadData");

const metricSharpe = document.getElementById("metricSharpe");
const metricHitRate = document.getElementById("metricHitRate");
const metricDrawdown = document.getElementById("metricDrawdown");
const metricGross = document.getElementById("metricGross");

const walkForwardTable = document.getElementById("walkForwardTable");
const qualityReport = document.getElementById("qualityReport");
const dataExplorerTable = document.getElementById("dataExplorerTable");
const providerStatus = document.getElementById("providerStatus");

const mmChartEl = document.getElementById("mmChart");
const pairsChartEl = document.getElementById("pairsChart");

let mmChart;
let pairsChart;
let lastExplorerData = [];

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

async function runDataExplorer() {
  const payload = {
    symbol: document.getElementById("dataSymbol").value,
    start: document.getElementById("dataStart").value,
    end: document.getElementById("dataEnd").value,
    interval: document.getElementById("dataInterval").value,
    source: document.getElementById("dataSource").value,
  };
  const res = await fetch(`${baseUrl()}/data/prices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Data explorer fetch failed");
  const data = await res.json();
  lastExplorerData = data || [];
  if (!data?.length) {
    dataExplorerTable.textContent = "No data returned.";
    return;
  }
  dataExplorerTable.innerHTML = data
    .slice(0, 10)
    .map(
      (row) =>
        `<div>${row.timestamp} | O:${row.price_open} H:${row.price_high} L:${row.price_low} C:${row.price_close} V:${row.volume}</div>`
    )
    .join("");
}

function downloadExplorerCsv() {
  if (!lastExplorerData.length) {
    dataExplorerTable.textContent = "No data to export.";
    return;
  }
  const headers = Object.keys(lastExplorerData[0]);
  const rows = [headers.join(",")].concat(
    lastExplorerData.map((row) => headers.map((h) => row[h]).join(","))
  );
  const blob = new Blob([rows.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "prices.csv";
  a.click();
  URL.revokeObjectURL(url);
}

async function refreshProviders() {
  const res = await fetch(`${baseUrl()}/providers/status`);
  if (!res.ok) throw new Error("Provider status fetch failed");
  const data = await res.json();
  if (!data?.length) {
    providerStatus.textContent = "No provider status yet.";
    return;
  }
  providerStatus.innerHTML = data
    .map(
      (row) =>
        `<div>${row.name}: ${row.status} (last_success: ${row.last_success || "n/a"})</div>`
    )
    .join("");
}

healthBtn.addEventListener("click", checkHealth);
runMarketMakerBtn.addEventListener("click", runMarketMaker);
runPairsBtn.addEventListener("click", runPairs);
runQualityBtn.addEventListener("click", runQuality);
runWalkForwardBtn.addEventListener("click", runWalkForward);
runDataExplorerBtn.addEventListener("click", runDataExplorer);
refreshProvidersBtn.addEventListener("click", refreshProviders);
downloadDataBtn.addEventListener("click", downloadExplorerCsv);
refreshAll.addEventListener("click", async () => {
  await runMarketMaker();
  await runPairs();
  await runQuality();
});

checkHealth();
