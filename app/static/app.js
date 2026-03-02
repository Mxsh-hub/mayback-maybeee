const API_PREFIX = "/api/v1";
const DEFAULT_DEMO_USER = "demo_user_001";

const outputPanel = document.getElementById("outputPanel");
const healthStatus = document.getElementById("healthStatus");
const quickHint = document.getElementById("quickHint");
const scoreSummary = document.getElementById("scoreSummary");
const dimensionGrid = document.getElementById("dimensionGrid");
const transactionsSummary = document.getElementById("transactionsSummary");
const transactionsTableWrap = document.getElementById("transactionsTableWrap");
const transactionsTableBody = document.getElementById("transactionsTableBody");

const demoUserIdInput = document.getElementById("demoUserId");
const classifyUserIdInput = document.getElementById("classifyUserId");
const scoreUserIdInput = document.getElementById("scoreUserId");
const viewUserIdInput = document.getElementById("viewUserId");

const classifyStartDateInput = document.getElementById("classifyStartDate");
const classifyEndDateInput = document.getElementById("classifyEndDate");
const scoreStartDateInput = document.getElementById("scoreStartDate");
const scoreEndDateInput = document.getElementById("scoreEndDate");
const viewStartDateInput = document.getElementById("viewStartDate");
const viewEndDateInput = document.getElementById("viewEndDate");

function printResult(title, payload, isError = false) {
  const stamp = new Date().toLocaleString();
  outputPanel.textContent = `[${stamp}] ${title}\n\n${JSON.stringify(payload, null, 2)}`;
  outputPanel.style.color = isError ? "#ffd0d0" : "#d7f8f2";
}

function setBusy(button, busy, busyText) {
  if (!button.dataset.originalText) {
    button.dataset.originalText = button.textContent;
  }

  if (busy) {
    button.disabled = true;
    button.textContent = busyText;
  } else {
    button.disabled = false;
    button.textContent = button.dataset.originalText;
  }
}

function readOptionalDates(startInput, endInput) {
  const body = {};
  if (startInput.value) {
    body.start_date = startInput.value;
  }
  if (endInput.value) {
    body.end_date = endInput.value;
  }
  return body;
}

function setUserAcrossForms(userId) {
  classifyUserIdInput.value = userId;
  scoreUserIdInput.value = userId;
  viewUserIdInput.value = userId;
}

function normalizeUserId() {
  const userId = demoUserIdInput.value.trim() || DEFAULT_DEMO_USER;
  demoUserIdInput.value = userId;
  setUserAcrossForms(userId);
  return userId;
}

function getDateRangeFromMonths(monthsCovered) {
  if (!Array.isArray(monthsCovered) || monthsCovered.length === 0) {
    return {};
  }

  const sorted = [...monthsCovered].sort();
  const firstMonth = sorted[0];
  const lastMonth = sorted[sorted.length - 1];

  const [year, month] = lastMonth.split("-").map(Number);
  const endDateObj = new Date(year, month, 0);
  const endYear = endDateObj.getFullYear();
  const endMonth = String(endDateObj.getMonth() + 1).padStart(2, "0");
  const endDay = String(endDateObj.getDate()).padStart(2, "0");

  return {
    start_date: `${firstMonth}-01`,
    end_date: `${endYear}-${endMonth}-${endDay}`
  };
}

function applyDateRange(range) {
  classifyStartDateInput.value = range.start_date || "";
  classifyEndDateInput.value = range.end_date || "";
  scoreStartDateInput.value = range.start_date || "";
  scoreEndDateInput.value = range.end_date || "";
}

function renderDimensionCards(scoreData) {
  const dimensions = scoreData.dimensions || {};
  const cards = Object.entries(dimensions).map(([name, payload]) => {
    const readable = name.replaceAll("_", " ");
    return `
      <div class="metric-card">
        <p class="metric-name">${readable}</p>
        <p class="metric-value">${payload.score} / 100</p>
      </div>
    `;
  });

  if (cards.length === 0) {
    dimensionGrid.classList.add("hidden");
    dimensionGrid.innerHTML = "";
    return;
  }

  dimensionGrid.innerHTML = cards.join("");
  dimensionGrid.classList.remove("hidden");
}

async function postJson(path, body) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  });

  const rawText = await response.text();
  let parsed = {};
  if (rawText.trim()) {
    try {
      parsed = JSON.parse(rawText);
    } catch (_err) {
      parsed = { raw: rawText };
    }
  }

  if (!response.ok) {
    const err = new Error(`HTTP ${response.status}`);
    err.details = parsed;
    throw err;
  }

  return parsed;
}

async function getJson(path, query) {
  const params = new URLSearchParams();
  if (query?.start_date) {
    params.set("start_date", query.start_date);
  }
  if (query?.end_date) {
    params.set("end_date", query.end_date);
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_PREFIX}${path}${suffix}`);

  const rawText = await response.text();
  let parsed = {};
  if (rawText.trim()) {
    try {
      parsed = JSON.parse(rawText);
    } catch (_err) {
      parsed = { raw: rawText };
    }
  }

  if (!response.ok) {
    const err = new Error(`HTTP ${response.status}`);
    err.details = parsed;
    throw err;
  }

  return parsed;
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    healthStatus.textContent = "online";
    healthStatus.classList.add("status-good");
    healthStatus.classList.remove("status-bad");
  } catch (_error) {
    healthStatus.textContent = "offline";
    healthStatus.classList.add("status-bad");
    healthStatus.classList.remove("status-good");
  }
}

async function seedSampleData(userId) {
  const seedResult = await postJson("/transactions/seed-sample", { user_id: userId });
  const range = getDateRangeFromMonths(seedResult.months_covered);
  applyDateRange(range);

  quickHint.textContent = `Seeded ${seedResult.transaction_count} transactions across ${seedResult.months_covered.join(", ")}. AI analysis is re-run on every classify/score request.`;
  return { seedResult, range };
}

function wireQuickDemo() {
  const seedDataBtn = document.getElementById("seedDataBtn");
  const runDemoBtn = document.getElementById("runDemoBtn");

  seedDataBtn.addEventListener("click", async () => {
    const userId = normalizeUserId();
    setBusy(seedDataBtn, true, "Seeding...");
    try {
      const result = await seedSampleData(userId);
      printResult("Seed Success", result.seedResult);
    } catch (error) {
      printResult("Seed Failed", error.details || { message: error.message }, true);
    } finally {
      setBusy(seedDataBtn, false, "Seeding...");
    }
  });

  runDemoBtn.addEventListener("click", async () => {
    const userId = normalizeUserId();
    setBusy(runDemoBtn, true, "Running...");
    scoreSummary.classList.add("hidden");
    dimensionGrid.classList.add("hidden");

    try {
      const { seedResult, range } = await seedSampleData(userId);
      const classifyResult = await postJson(
        `/transactions/classify/${encodeURIComponent(userId)}`,
        range
      );
      const scoreResult = await postJson(
        `/trust-index/${encodeURIComponent(userId)}`,
        range
      );

      scoreSummary.classList.remove("hidden");
      scoreSummary.textContent = `Trust Index: ${scoreResult.trust_index} / 100 from ${scoreResult.tx_count} transactions.`;
      renderDimensionCards(scoreResult);

      printResult("Full Demo Success", {
        seed: seedResult,
        classify: classifyResult,
        score: {
          trust_index: scoreResult.trust_index,
          tx_count: scoreResult.tx_count,
          computed_at: scoreResult.computed_at
        }
      });
    } catch (error) {
      printResult("Full Demo Failed", error.details || { message: error.message }, true);
    } finally {
      setBusy(runDemoBtn, false, "Running...");
    }
  });
}

function wireClassify() {
  const classifyBtn = document.getElementById("classifyBtn");
  classifyBtn.addEventListener("click", async () => {
    const userId = (classifyUserIdInput.value || demoUserIdInput.value).trim();
    if (!userId) {
      printResult("Classification Failed", { message: "User ID is required." }, true);
      return;
    }

    setBusy(classifyBtn, true, "Classifying...");
    try {
      const body = readOptionalDates(classifyStartDateInput, classifyEndDateInput);
      const data = await postJson(`/transactions/classify/${encodeURIComponent(userId)}`, body);
      printResult("Classification Success", data);
    } catch (error) {
      printResult("Classification Failed", error.details || { message: error.message }, true);
    } finally {
      setBusy(classifyBtn, false, "Classifying...");
    }
  });
}

function wireScore() {
  const scoreBtn = document.getElementById("scoreBtn");
  scoreBtn.addEventListener("click", async () => {
    const userId = (scoreUserIdInput.value || demoUserIdInput.value).trim();
    if (!userId) {
      printResult("Scoring Failed", { message: "User ID is required." }, true);
      return;
    }

    setBusy(scoreBtn, true, "Scoring...");
    try {
      const body = readOptionalDates(scoreStartDateInput, scoreEndDateInput);
      const data = await postJson(`/trust-index/${encodeURIComponent(userId)}`, body);
      printResult("Trust Index Success", data);

      scoreSummary.classList.remove("hidden");
      scoreSummary.textContent = `Trust Index: ${data.trust_index} / 100 from ${data.tx_count} transactions.`;
      renderDimensionCards(data);
    } catch (error) {
      scoreSummary.classList.add("hidden");
      dimensionGrid.classList.add("hidden");
      printResult("Scoring Failed", error.details || { message: error.message }, true);
    } finally {
      setBusy(scoreBtn, false, "Scoring...");
    }
  });
}

function renderTransactionsTable(data) {
  const rows = data.transactions || [];
  if (rows.length === 0) {
    transactionsSummary.classList.remove("hidden");
    transactionsSummary.textContent = "No transactions found for this user in the selected range.";
    transactionsTableBody.innerHTML = "";
    transactionsTableWrap.classList.add("hidden");
    return;
  }

  const html = rows.map((row) => `
    <tr>
      <td>${row.txn_date || "-"}</td>
      <td>${row.description || "-"}</td>
      <td>${row.amount}</td>
      <td>${row.direction || "-"}</td>
      <td>${row.transaction_ref || "-"}</td>
      <td>${row.source || "-"}</td>
      <td>${row.category || "-"}</td>
      <td>${row.intent_label || "-"}</td>
      <td>${row.essentiality ?? "-"}</td>
      <td>${row.model_name || "-"}</td>
      <td>${row.created_at || "-"}</td>
      <td>${row.updated_at || "-"}</td>
    </tr>
  `).join("");

  transactionsTableBody.innerHTML = html;
  transactionsSummary.classList.remove("hidden");
  transactionsSummary.textContent = `Loaded ${rows.length} transactions for user ${data.user_id}.`;
  transactionsTableWrap.classList.remove("hidden");
}

function wireTransactionsView() {
  const viewTransactionsBtn = document.getElementById("viewTransactionsBtn");
  viewTransactionsBtn.addEventListener("click", async () => {
    const userId = (viewUserIdInput.value || demoUserIdInput.value).trim();
    if (!userId) {
      printResult("Load Transactions Failed", { message: "User ID is required." }, true);
      return;
    }

    setBusy(viewTransactionsBtn, true, "Loading...");
    try {
      const query = readOptionalDates(viewStartDateInput, viewEndDateInput);
      const data = await getJson(`/transactions/user/${encodeURIComponent(userId)}`, query);
      renderTransactionsTable(data);
      // Show every returned transaction detail in the Response panel.
      printResult("Transactions Loaded", data);
    } catch (error) {
      transactionsSummary.classList.add("hidden");
      transactionsTableWrap.classList.add("hidden");
      printResult("Load Transactions Failed", error.details || { message: error.message }, true);
    } finally {
      setBusy(viewTransactionsBtn, false, "Loading...");
    }
  });
}

checkHealth();
wireQuickDemo();
wireClassify();
wireScore();
wireTransactionsView();
