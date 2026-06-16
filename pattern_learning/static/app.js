const state = {
  candidates: [],
  current: null,
  config: { routes: [], operators: [] },
  mode: "pattern",
};

const $ = (selector) => document.querySelector(selector);

// plm と accumulation はどちらも expected(JSON)を編集して承認する意味モード。
const isSemanticMode = () => state.mode === "plm" || state.mode === "accumulation";
const cardLabel = (candidate) =>
  candidate.suggested_route
  || candidate.expected?.primary_intent
  || candidate.expected?.intent
  || "?";

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Request failed");
  return payload;
}

function toast(message, isError = false) {
  const node = $("#toast");
  node.textContent = message;
  node.className = isError ? "visible error" : "visible";
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => {
    node.className = "";
  }, 3500);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function loadStats() {
  if (state.mode === "accumulation") {
    const stats = await api("/api/accumulation/stats");
    $("#pendingLabel").textContent = "未レビュー";
    $("#approvedLabel").textContent = `承認 (${stats.required_reviewed}必要)`;
    $("#rejectedLabel").textContent = "却下";
    $("#modelLabel").textContent = "収集";
    $("#pendingCount").textContent = stats.cases.pending;
    $("#patternCount").textContent = stats.cases.approved;
    $("#rejectedCount").textContent = stats.cases.rejected;
    $("#modelStatus").textContent =
      `${stats.collected}/${stats.target}件 (締切 ${stats.deadline_at.slice(0, 10)})`;
    return;
  }
  if (state.mode === "plm") {
    const stats = await api("/api/plm/stats");
    $("#pendingLabel").textContent = "未評価Case";
    $("#approvedLabel").textContent = "承認済み";
    $("#rejectedLabel").textContent = "却下";
    $("#modelLabel").textContent = "Benchmark";
    $("#pendingCount").textContent = stats.cases.pending;
    $("#patternCount").textContent = stats.cases.approved;
    $("#rejectedCount").textContent = stats.cases.rejected;
    $("#modelStatus").textContent =
      `${stats.benchmark_review_status} / ${stats.total}件`;
    return;
  }
  const stats = await api("/api/stats");
  $("#pendingLabel").textContent = "未評価";
  $("#approvedLabel").textContent = "承認Pattern";
  $("#rejectedLabel").textContent = "却下";
  $("#modelLabel").textContent = "最新モデル";
  $("#pendingCount").textContent = stats.candidates.pending;
  $("#patternCount").textContent = stats.patterns;
  $("#rejectedCount").textContent = stats.candidates.rejected;
  const latest = stats.latest_training_run;
  $("#modelStatus").textContent = latest
    ? `${latest.sample_count}件 / ${latest.created_at.slice(0, 10)}`
    : "未学習";
}

async function loadCandidates(preferredId = null) {
  const status = $("#statusFilter").value;
  let endpoint;
  if (state.mode === "accumulation") {
    endpoint = `/api/accumulation/cases?status=${status}`
      + `&category=${$("#categoryFilter").value}`;
  } else if (state.mode === "plm") {
    endpoint = `/api/plm/cases?status=${status}&split=${$("#splitFilter").value}`;
  } else {
    endpoint = `/api/candidates?status=${status}&limit=100`;
  }
  const payload = await api(endpoint);
  state.candidates = payload.items;
  renderCandidateList();
  const selected = state.candidates.find((item) => item.id === preferredId)
    || state.candidates[0];
  selectCandidate(selected || null);
}

function renderCandidateList() {
  const list = $("#candidateList");
  if (!state.candidates.length) {
    list.innerHTML = `<div class="queue-empty">この状態の候補はありません。</div>`;
    return;
  }
  list.innerHTML = state.candidates.map((candidate) => `
    <button class="candidate-card ${state.current?.id === candidate.id ? "active" : ""}"
      data-id="${escapeHtml(candidate.id)}">
      <div class="candidate-meta">
        <span class="route-dot route-${escapeHtml(cardLabel(candidate))}"></span>
        <strong>${escapeHtml(cardLabel(candidate))}</strong>
        <small>#${candidate.id}</small>
      </div>
      <p>${escapeHtml(candidate.input_text)}</p>
      <div class="candidate-source">${escapeHtml(
        state.mode === "plm"
          ? `${candidate.split} / ${candidate.language} / ${candidate.status}`
          : state.mode === "accumulation"
            ? `${candidate.category} / ${candidate.language} / ${candidate.status}`
              + `${candidate.critical_underprocessing ? " / ⚠critical" : ""}`
            : candidate.source.title
      )}</div>
    </button>
  `).join("");
  list.querySelectorAll(".candidate-card").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.id;
      selectCandidate(state.candidates.find((item) => String(item.id) === id));
      renderCandidateList();
    });
  });
}

function selectCandidate(candidate) {
  state.current = candidate;
  $("#emptyState").classList.toggle("hidden", Boolean(candidate));
  $("#reviewForm").classList.toggle("hidden", !candidate);
  if (!candidate) return;

  $("#sourceKind").textContent = candidate.source.kind;
  $("#sourceLink").textContent = candidate.source.title;
  $("#sourceLink").href = candidate.source.url || "#";
  $("#revisionId").textContent = `rev. ${candidate.source.revision_id}`;
  $("#candidateText").textContent = candidate.input_text;
  $("#patternReviewFields").classList.toggle("hidden", isSemanticMode());
  $("#plmReviewFields").classList.toggle("hidden", !isSemanticMode());
  $("#reviewNotes").value = candidate.notes || "";

  if (state.mode === "accumulation") {
    $("#semanticNotice").textContent =
      "この承認はaccumulationレビューログだけへ保存され、sealed v2測定ゲートの"
      + "「人間承認」件数に反映されます。修正したexpectedは測定の正解にもなります。";
    $("#plmMetadata").innerHTML = [
      `category: ${candidate.category}`,
      `language: ${candidate.language}`,
      `status: ${candidate.status}`,
      candidate.critical_underprocessing ? "⚠ critical-underprocessing対象" : "",
      `case: ${candidate.id}`,
    ].filter(Boolean).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
    $("#expectedSemantics").value = JSON.stringify(candidate.expected, null, 2);
    return;
  }

  if (state.mode === "plm") {
    $("#semanticNotice").textContent =
      "この承認はPLM review logだけへ保存され、Pattern Routerの学習DBには入りません。";
    $("#plmMetadata").innerHTML = [
      `split: ${candidate.split}`,
      `language: ${candidate.language}`,
      `status: ${candidate.status}`,
      `case: ${candidate.id}`,
    ].map((item) => `<span>${escapeHtml(item)}</span>`).join("");
    $("#expectedSemantics").value = JSON.stringify(candidate.expected, null, 2);
    return;
  }

  $("#routeSelect").value = candidate.suggested_route;
  $("#thoughtForm").value = JSON.stringify(candidate.thought_form, null, 2);
  $("#ratingSelect").value = candidate.status === "rejected" ? "2" : "4";
  const confidence = Math.round(candidate.confidence * 100);
  $("#confidenceBar").style.width = `${confidence}%`;
  $("#confidenceValue").textContent = `${confidence}%`;

  document.querySelectorAll("[data-operator]").forEach((input) => {
    input.checked = candidate.suggested_operators.includes(input.value);
  });
}

function renderConfig() {
  $("#routeSelect").innerHTML = state.config.routes
    .map((route) => `<option value="${route}">${route}</option>`)
    .join("");
  $("#operatorGrid").innerHTML = state.config.operators.map((operator) => `
    <label class="operator-chip">
      <input type="checkbox" data-operator value="${operator}">
      <span>${operator.replaceAll("_", " ")}</span>
    </label>
  `).join("");
}

function reviewPayload(verdict) {
  if (isSemanticMode()) {
    let expected;
    try {
      expected = JSON.parse($("#expectedSemantics").value);
    } catch (_error) {
      throw new Error("Expected Semantic Packetが正しいJSONではありません");
    }
    return {
      case_id: state.current.id,
      verdict,
      expected,
      notes: $("#reviewNotes").value,
    };
  }
  let thoughtForm;
  try {
    thoughtForm = JSON.parse($("#thoughtForm").value);
  } catch (_error) {
    throw new Error("Thought Formが正しいJSONではありません");
  }
  return {
    candidate_id: state.current.id,
    verdict,
    rating: Number($("#ratingSelect").value),
    route: $("#routeSelect").value,
    operators: [...document.querySelectorAll("[data-operator]:checked")]
      .map((input) => input.value),
    thought_form: thoughtForm,
    notes: $("#reviewNotes").value,
  };
}

async function submitReview(verdict) {
  if (!state.current) return;
  const nextIndex = state.candidates.findIndex((item) => item.id === state.current.id) + 1;
  const nextId = state.candidates[nextIndex]?.id || null;
  const endpoint = state.mode === "plm"
    ? "/api/plm/reviews"
    : state.mode === "accumulation"
      ? "/api/accumulation/reviews"
      : "/api/reviews";
  await api(endpoint, {
    method: "POST",
    body: JSON.stringify(reviewPayload(verdict)),
  });
  const approvedMessage = state.mode === "plm"
    ? "PLM review logへ承認内容を保存しました"
    : state.mode === "accumulation"
      ? "accumulationレビューログへ承認しました（ゲートの承認件数に反映）"
      : "Pattern DBへ承認しました";
  toast(verdict === "approve" ? approvedMessage : "候補を却下しました");
  await Promise.all([loadStats(), loadCandidates(nextId)]);
}

async function runImport(event) {
  event.preventDefault();
  if (event.submitter?.value === "cancel") {
    $("#importDialog").close();
    return;
  }
  const button = $("#runImport");
  button.disabled = true;
  button.textContent = "取得中...";
  try {
    const userAgent = $("#wikiUserAgent").value.trim();
    localStorage.setItem("patternLabUserAgent", userAgent);
    const result = await api("/api/import/wikipedia", {
      method: "POST",
      body: JSON.stringify({
        titles: $("#wikiTitles").value.split("\n").filter(Boolean),
        category: $("#wikiCategory").value,
        user_agent: userAgent,
        article_limit: Number($("#articleLimit").value),
        patterns_per_article: Number($("#patternsPerArticle").value),
      }),
    });
    $("#importDialog").close();
    toast(`${result.articles}記事から${result.candidates_inserted}件を追加しました`);
    await Promise.all([loadStats(), loadCandidates()]);
  } catch (error) {
    toast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "評価キューへ追加";
  }
}

async function trainModel() {
  const button = $("#trainModel");
  button.disabled = true;
  button.textContent = "学習中...";
  try {
    const result = await api("/api/train", {
      method: "POST",
      body: JSON.stringify({ epochs: 24, dimension: 2048 }),
    });
    const accuracy = result.metrics.validation_accuracy;
    const summary = accuracy === null
      ? `${result.sample_count}件で学習（評価用データはまだ不足）`
      : `${result.sample_count}件で学習 / 検証精度 ${Math.round(accuracy * 100)}%`;
    if (result.gate?.passed) {
      toast(`${summary} / ゲート合格。「ゲート検証して昇格」で反映できます`);
    } else {
      const misses = [
        ...(result.gate?.checks?.frozen_regression?.raw_misses ?? []),
        ...(result.gate?.checks?.foundation_anchors?.raw_misses ?? []),
      ].length;
      toast(`${summary} / ゲート不合格(${misses}件)。デプロイは未更新、候補のみ保存`, true);
    }
    await loadStats();
  } catch (error) {
    toast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "承認データで学習";
  }
}

async function boot() {
  try {
    state.config = await api("/api/config");
    renderConfig();
    await loadAccumulationCategories();
    $("#wikiUserAgent").value = localStorage.getItem("patternLabUserAgent") || "";
    updateMode();
    await Promise.all([loadStats(), loadCandidates()]);
  } catch (error) {
    toast(error.message, true);
  }
}

$("#statusFilter").addEventListener("change", () => loadCandidates());
$("#splitFilter").addEventListener("change", () => loadCandidates());
$("#categoryFilter").addEventListener("change", () => loadCandidates());
$("#reviewMode").addEventListener("change", async () => {
  state.mode = $("#reviewMode").value;
  state.current = null;
  updateMode();
  try {
    await Promise.all([loadStats(), loadCandidates()]);
  } catch (error) {
    toast(error.message, true);
  }
});
$("#reviewForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await submitReview("approve");
  } catch (error) {
    toast(error.message, true);
  }
});
$("#rejectCandidate").addEventListener("click", async () => {
  try {
    await submitReview("reject");
  } catch (error) {
    toast(error.message, true);
  }
});
async function promoteModel() {
  const button = $("#promoteModel");
  button.disabled = true;
  button.textContent = "ゲート検証中...";
  try {
    const report = await api("/api/promote", {
      method: "POST",
      body: JSON.stringify({}),
    });
    if (report.promoted) {
      toast("ゲート合格。デプロイモデルを更新しました（旧モデルは履歴へ保存）");
    } else {
      const misses = [
        ...(report.checks?.frozen_regression?.raw_misses ?? []),
        ...(report.checks?.foundation_anchors?.raw_misses ?? []),
      ].length;
      toast(`ゲート不合格(${misses}件)。デプロイは変更されていません`, true);
    }
    await loadStats();
  } catch (error) {
    toast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "ゲート検証して昇格";
  }
}

$("#openImport").addEventListener("click", () => $("#importDialog").showModal());
$("#importForm").addEventListener("submit", runImport);
$("#trainModel").addEventListener("click", trainModel);
$("#promoteModel").addEventListener("click", promoteModel);

boot();

function updateMode() {
  const isPlm = state.mode === "plm";
  const isAccum = state.mode === "accumulation";
  $("#patternActions").classList.toggle("hidden", isSemanticMode());
  $("#splitFilter").classList.toggle("hidden", !isPlm);
  $("#categoryFilter").classList.toggle("hidden", !isAccum);
  $(".section-kicker").textContent = isPlm
    ? "PLM BENCHMARK REVIEW"
    : isAccum
      ? "V2 READINESS REVIEW"
      : "REVIEW QUEUE";
  $(".queue-panel h2").textContent = isSemanticMode()
    ? "Semantic Case"
    : "評価候補";
  $("#emptyState h2").textContent = isSemanticMode()
    ? "Semantic Caseを選択してください"
    : "候補を選択してください";
  $("#emptyState p").textContent = isPlm
    ? "期待Semantic Packetを確認し、必要ならJSONを修正して承認します。"
    : isAccum
      ? "expected(intent/processing_class/core_mode)を確認・修正して承認すると、"
        + "sealed v2測定ゲートの承認件数に反映されます。"
      : "推定結果を修正して承認すると、Pattern DBの学習資産になります。";
}

async function loadAccumulationCategories() {
  try {
    const config = await api("/api/accumulation/config");
    $("#categoryFilter").innerHTML = config.categories
      .map((category) => `<option value="${category}">${
        category === "all" ? "全カテゴリ" : category
      }</option>`)
      .join("");
  } catch (_error) {
    // campaign 未配置でも他モードは動かす
  }
}
