"use strict";

/* ==========================================================================
   AudioLocal — front-end
   ========================================================================== */

const POLL_INTERVAL_MS = 1000;
const SUBMIT_LABEL = "Converter para MP3";

const els = {
  form: document.querySelector("#convert-form"),
  urlInput: document.querySelector("#url"),
  submitBtn: document.querySelector("#convert-btn"),
  notice: document.querySelector("#notice"),
  progressCard: document.querySelector("#progress-card"),
  progressTrack: document.querySelector("#progress-track"),
  progressBar: document.querySelector("#progress-bar"),
  progressPercent: document.querySelector("#progress-percent"),
  progressMessage: document.querySelector("#progress-message"),
  taskTitle: document.querySelector("#task-title"),
  downloadLink: document.querySelector("#download-link"),
  historyList: document.querySelector("#history-list"),
  refreshBtn: document.querySelector("#refresh-btn"),
};

let pollTimer = null;

/* ---------- Utilitários ---------- */

async function requestJson(url, options, fallbackError) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || fallbackError);
  return data;
}

function createElement(tag, { text = "", className = "" } = {}) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

function formatDate(value) {
  if (!value) return "Data desconhecida";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("pt-BR");
}

function downloadUrl(filename) {
  return `/downloads/${encodeURIComponent(filename)}`;
}

/* ---------- Avisos ---------- */

function showNotice(message, kind = "error") {
  els.notice.textContent = message;
  els.notice.dataset.kind = kind;
  els.notice.hidden = false;
}

function hideNotice() {
  els.notice.textContent = "";
  els.notice.hidden = true;
}

/* ---------- Formulário ---------- */

function setSubmitting(isSubmitting, label = SUBMIT_LABEL) {
  els.submitBtn.disabled = isSubmitting;
  els.submitBtn.textContent = label;
}

/* ---------- Progresso ---------- */

function setProgress(percent) {
  const isKnown = percent !== null && percent !== undefined;
  els.progressTrack.classList.toggle("is-indeterminate", !isKnown);

  if (!isKnown) {
    els.progressPercent.textContent = "…";
    els.progressTrack.removeAttribute("aria-valuenow");
    return;
  }

  const value = Math.max(0, Math.min(100, Number(percent)));
  els.progressBar.style.width = `${value}%`;
  els.progressPercent.textContent = `${value}%`;
  els.progressTrack.setAttribute("aria-valuenow", value);
}

function resetProgress() {
  els.progressCard.hidden = false;
  els.downloadLink.hidden = true;
  els.taskTitle.textContent = "Preparando conversão";
  els.progressMessage.textContent = "Conectando à fonte…";
  setProgress(0);
}

function renderTask(task) {
  els.taskTitle.textContent = task.title || "Conversão em andamento";
  els.progressMessage.textContent = task.message || "Processando…";
  setProgress(task.progress);
}

function showDownload(filename) {
  els.downloadLink.href = downloadUrl(filename);
  els.downloadLink.hidden = false;
}

/* ---------- Acompanhamento da tarefa ---------- */

function stopPolling() {
  clearTimeout(pollTimer);
  pollTimer = null;
}

async function finishTask(task) {
  stopPolling();
  setSubmitting(false);

  if (task.state === "completed") {
    setProgress(100);
    showDownload(task.filename);
  } else {
    showNotice(task.error || task.message || "A conversão falhou.");
  }
  await loadHistory();
}

function startPolling(taskId) {
  stopPolling();

  const tick = async () => {
    try {
      const task = await requestJson(
        `/api/tasks/${encodeURIComponent(taskId)}`,
        undefined,
        "Não foi possível consultar a tarefa."
      );
      renderTask(task);

      if (task.state === "completed" || task.state === "failed") {
        await finishTask(task);
        return;
      }
      pollTimer = setTimeout(tick, POLL_INTERVAL_MS);
    } catch (error) {
      stopPolling();
      setSubmitting(false);
      showNotice(error.message || "Erro ao acompanhar a conversão.");
    }
  };

  tick();
}

async function handleSubmit(event) {
  event.preventDefault();
  hideNotice();

  const url = els.urlInput.value.trim();
  const bitrate = new FormData(els.form).get("bitrate");

  setSubmitting(true, "Iniciando…");
  resetProgress();

  try {
    const { id } = await requestJson(
      "/api/convert",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, bitrate }),
      },
      "Não foi possível iniciar a conversão."
    );
    setSubmitting(true, "Convertendo…");
    startPolling(id);
  } catch (error) {
    showNotice(error.message || "Erro ao iniciar a conversão.");
    els.progressCard.hidden = true;
    setSubmitting(false);
  }
}

/* ---------- Histórico ---------- */

function createHistoryAction(item) {
  const action = createElement("div", { className: "history-action" });

  if (item.status === "completed" && item.filename) {
    const link = createElement("a", { text: "Baixar MP3", className: "download-small" });
    link.href = downloadUrl(item.filename);
    action.append(link);
    return action;
  }

  const label = createElement("span", { text: "Falhou", className: "failed-label" });
  if (item.error) label.title = item.error;
  action.append(label);
  return action;
}

function createHistoryItem(item) {
  const row = createElement("article", { className: "history-item" });

  const meta = createElement("div", { className: "history-meta" });
  meta.append(
    createElement("span", { text: formatDate(item.created_at) }),
    createElement("span", { text: `${item.bitrate} kbps`, className: "chip" })
  );

  const main = createElement("div", { className: "history-main" });
  main.append(
    createElement("strong", { text: item.title || "Conversão sem título", className: "history-title" }),
    meta
  );

  row.append(main, createHistoryAction(item));
  return row;
}

function renderHistory(items) {
  if (!items.length) {
    els.historyList.replaceChildren(
      createElement("p", {
        text: "Nenhuma conversão ainda. Cole um link acima para começar.",
        className: "muted",
      })
    );
    return;
  }
  els.historyList.replaceChildren(...items.map(createHistoryItem));
}

async function loadHistory() {
  try {
    const items = await requestJson("/api/history", undefined, "Falha ao carregar o histórico.");
    renderHistory(items);
  } catch {
    els.historyList.replaceChildren(
      createElement("p", { text: "Não foi possível carregar o histórico.", className: "muted" })
    );
  }
}

/* ---------- Inicialização ---------- */

els.form.addEventListener("submit", handleSubmit);
els.refreshBtn.addEventListener("click", loadHistory);
loadHistory();