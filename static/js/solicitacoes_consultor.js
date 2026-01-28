// static/js/solicitacoes_consultor.js
document.addEventListener("DOMContentLoaded", () => {
  const q = document.getElementById("q");
  const fTipo = document.getElementById("f_tipo");
  const fProto = document.getElementById("f_protocolo");
  const fStatus = document.getElementById("f_status");

  const list = document.getElementById("list");
  if (!list) return;

  const cards = Array.from(list.querySelectorAll(".req-card"));
  const emptyState =
    document.getElementById("emptyState") || list.querySelector(".empty-state");

  // =========================
  // Helpers
  // =========================
  const normText = (v) =>
    (v ?? "")
      .toString()
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");

  const onlyDigits = (v) => (v ?? "").toString().replace(/\D+/g, "");

  const isAll = (v) => {
    const x = normText(v);
    return x === "" || x === "todos";
  };

  function setEmpty(show) {
    if (!emptyState) return;
    emptyState.style.display = show ? "block" : "none";
  }

  function isFinalizado(statusText) {
    return normText(statusText) === "finalizado";
  }

  function isNaoAprovado(statusText) {
    return normText(statusText) === "nao aprovado";
  }

  // Mostra/oculta a caixa de finalização/justificativa dentro do card
  function toggleFinalizacao(card, statusText) {
    const box = card.querySelector(".finalizacao-box");
    if (!box) return;

    const show = isFinalizado(statusText) || isNaoAprovado(statusText);
    box.hidden = !show;

    // Ajustes de UI para modo "Não Aprovado" (mostrar justificativa, sem anexo)
    const title1 = box.querySelector(".consultor-avaliacao__title"); // 1º título
    const lbl = box.querySelector(".consultor-label");
    const textarea = box.querySelector(".consultor-textarea");

    const uploadTitle = box.querySelector(
      '.consultor-avaliacao__title[style*="margin-top:14px"]'
    );
    const uploadBox = box.querySelector(".upload-box");

    if (isNaoAprovado(statusText)) {
      if (title1) title1.textContent = "Justificativa para o cliente";
      if (lbl) lbl.innerHTML = 'Escreva a justificativa <span class="req">*</span>';
      if (textarea) {
        textarea.placeholder = "Ex: Motivo do não aprovado e orientações para correção...";
      }

      // esconder anexo no "Não Aprovado"
      if (uploadTitle) uploadTitle.style.display = "none";
      if (uploadBox) uploadBox.style.display = "none";
    } else {
      // Finalizado (volta ao normal)
      if (title1) title1.textContent = "Orientações para o cliente";
      if (lbl) lbl.innerHTML = 'Escreva orientações importantes <span class="req">*</span>';
      if (textarea) {
        textarea.placeholder = "Ex: Comparecer com documento e guias de 5 dias, etc...";
      }

      if (uploadTitle) uploadTitle.style.display = "";
      if (uploadBox) uploadBox.style.display = "";
    }
  }

  function setMsg(card, type, text) {
    const el = card.querySelector(".final-msg");
    if (!el) return;
    el.classList.remove("is-ok", "is-err");
    el.classList.add(type === "ok" ? "is-ok" : "is-err");
    el.textContent = text || "";
    el.hidden = !text;
  }

  // =========================
  // Indexa cards 1x
  // =========================
  const index = new Map();
  cards.forEach((card) => {
    const user = card.dataset.user || "";
    const cpf = card.dataset.cpf || "";
    const proto = card.dataset.proto || "";
    const fullText = card.textContent || "";

    index.set(card, {
      text: normText(`${user} ${cpf} ${proto} ${fullText}`),
      digits: onlyDigits(`${cpf} ${fullText}`),
    });
  });

  // =========================
  // Filtros
  // =========================
  function applyFilters() {
    const termRaw = normText(q?.value);
    const termDigits = onlyDigits(q?.value);

    const tipo = normText(fTipo?.value);
    const proto = normText(fProto?.value);
    const status = normText(fStatus?.value);

    let visible = 0;

    cards.forEach((card) => {
      const i = index.get(card);

      let okSearch = true;
      if (termRaw) {
        okSearch = termDigits ? i.digits.includes(termDigits) : i.text.includes(termRaw);
      }

      const cardTipo = normText(card.dataset.tipo);
      const cardProto = normText(card.dataset.proto);
      const cardStatus = normText(card.dataset.status);

      const okTipo = isAll(tipo) || cardTipo === tipo;
      const okProto = isAll(proto) || cardProto === proto;
      const okStatus = isAll(status) || cardStatus === status;

      const show = okSearch && okTipo && okProto && okStatus;
      card.style.display = show ? "" : "none";
      if (show) visible++;
    });

    setEmpty(visible === 0);
  }

  q?.addEventListener("input", applyFilters);
  fTipo?.addEventListener("change", applyFilters);
  fProto?.addEventListener("change", applyFilters);
  fStatus?.addEventListener("change", applyFilters);

  // =========================
  // Toggle detalhes
  // =========================
  list.addEventListener("click", (e) => {
    const btn = e.target.closest(".toggle");
    if (!btn) return;

    const card = btn.closest(".req-card");
    const body = card?.querySelector(".req-body");
    if (!body) return;

    const expanded = btn.getAttribute("aria-expanded") === "true";
    btn.setAttribute("aria-expanded", expanded ? "false" : "true");
    body.hidden = expanded;
  });

  // =========================
  // Badge helpers
  // =========================
  function statusSlug(statusText) {
    return normText(statusText).replace(/\s+/g, "-");
  }

  function ensureBadge(card) {
    const protoBox = card.querySelector(".proto");
    if (!protoBox) return null;

    let badge = protoBox.querySelector(".badge");
    if (!badge) {
      badge = document.createElement("span");
      badge.className = "badge";
      protoBox.appendChild(badge);
    }
    return badge;
  }

  function setBadge(card, newStatusText) {
    const badge = ensureBadge(card);
    if (!badge) return;

    badge.className = "badge";
    badge.classList.add(`badge-${statusSlug(newStatusText)}`);
    badge.textContent = newStatusText;

    // dataset para filtros
    card.dataset.status = normText(newStatusText);
  }

  // =========================
  // Mostrar/ocultar FINALIZAÇÃO no LOAD
  // =========================
  cards.forEach((card) => toggleFinalizacao(card, card.dataset.status || ""));

  // Preview ao trocar select
  list.addEventListener("change", (e) => {
    const sel = e.target.closest(".status-select");
    if (!sel) return;

    const card = sel.closest(".req-card");
    if (!card) return;

    toggleFinalizacao(card, sel.value || "");
  });

  // =========================
  // Atualizar nome do arquivo (input change)
  // =========================
  list.addEventListener("change", (e) => {
    const input = e.target.closest(".consultor-file");
    if (!input) return;

    const box = input.closest(".upload-box");
    const label = box?.querySelector(".upload-filename");
    if (!label) return;

    const file = input.files && input.files[0];
    label.textContent = file ? file.name : "Nenhum arquivo selecionado";
  });

  // =========================
  // Clique na caixa -> abrir seletor
  // =========================
  list.addEventListener("click", (e) => {
    const ui = e.target.closest(".upload-ui");
    if (!ui) return;

    const box = ui.closest(".upload-box");
    const input = box?.querySelector(".consultor-file");
    if (input) input.click();
  });

  // =========================
  // Drag & drop
  // =========================
  function preventDefaults(ev) {
    ev.preventDefault();
    ev.stopPropagation();
  }

  list.addEventListener("dragover", (e) => {
    const ui = e.target.closest(".upload-ui");
    if (!ui) return;
    preventDefaults(e);
    ui.classList.add("is-drag");
  });

  list.addEventListener("dragleave", (e) => {
    const ui = e.target.closest(".upload-ui");
    if (!ui) return;
    preventDefaults(e);
    ui.classList.remove("is-drag");
  });

  list.addEventListener("drop", (e) => {
    const ui = e.target.closest(".upload-ui");
    if (!ui) return;
    preventDefaults(e);
    ui.classList.remove("is-drag");

    const box = ui.closest(".upload-box");
    const input = box?.querySelector(".consultor-file");
    const label = box?.querySelector(".upload-filename");
    if (!input || !e.dataTransfer?.files?.length) return;

    const file = e.dataTransfer.files[0];
    input.files = e.dataTransfer.files;
    if (label) label.textContent = file ? file.name : "Nenhum arquivo selecionado";
  });

  // =========================
  // Atualizar status (DB + UI)
  // =========================
  list.addEventListener("click", async (e) => {
    const btnSave = e.target.closest(".btn-save-status");
    if (!btnSave) return;

    const card = btnSave.closest(".req-card");
    const select = card?.querySelector(".status-select");
    if (!card || !select) return;

    const protocolo = btnSave.dataset.protocolo || "";
    const origem = btnSave.dataset.origem || "";
    const newStatus = select.value || "";

    if (!protocolo || !origem || !newStatus) {
      setMsg(card, "err", "Dados inválidos para atualizar o status.");
      return;
    }

    const oldText = btnSave.textContent;
    btnSave.disabled = true;
    btnSave.textContent = "Salvando...";

    try {
      const resp = await fetch("/api/solicitacoes/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ protocolo, origem, status: newStatus }),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok || !data.ok) {
        setMsg(card, "err", "Erro ao atualizar status: " + (data.error || "erro desconhecido"));
        return;
      }

      setBadge(card, newStatus);
      toggleFinalizacao(card, newStatus);
      setMsg(card, "ok", "Status atualizado com sucesso!");
      applyFilters();
    } catch (err) {
      setMsg(card, "err", "Erro de conexão ao salvar o status.");
    } finally {
      btnSave.disabled = false;
      btnSave.textContent = oldText;
    }
  });

  // =========================
  // Salvar Avaliação / Justificativa (texto + PDF SOMENTE no Finalizado)
  // =========================
  list.addEventListener("click", async (e) => {
    const btn = e.target.closest(".btn-save-avaliacao");
    if (!btn) return;

    const card = btn.closest(".req-card");
    if (!card) return;

    const st = card.dataset.status || "";
    const finalizado = isFinalizado(st);
    const naoAprovado = isNaoAprovado(st);

    if (!finalizado && !naoAprovado) {
      setMsg(
        card,
        "err",
        "Para salvar, primeiro salve o status como 'Finalizado' ou 'Não Aprovado'."
      );
      return;
    }

    const protocolo = btn.dataset.protocolo || "";
    const origem = btn.dataset.origem || "";
    const textarea = card.querySelector(".consultor-textarea");
    const fileInput = card.querySelector(".consultor-file");

    if (!protocolo || !origem) {
      setMsg(card, "err", "Dados inválidos para salvar.");
      return;
    }

    if (!textarea || !textarea.value.trim()) {
      setMsg(card, "err", naoAprovado ? "Escreva a justificativa." : "Escreva as orientações para o cliente.");
      return;
    }

    const formData = new FormData();
    formData.append("protocolo", protocolo);
    formData.append("origem", origem);
    formData.append("resposta", textarea.value.trim());

    // ✅ Regra pedida:
    // - Finalizado: pode anexar PDF
    // - Não Aprovado: NÃO pode anexar documento (ignora mesmo se tiver)
    if (finalizado && fileInput && fileInput.files && fileInput.files.length > 0) {
      formData.append("arquivo", fileInput.files[0]);
    }

    const oldText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Salvando...";

    try {
      const resp = await fetch("/api/solicitacoes/finalizar", {
        method: "POST",
        body: formData,
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok || !data.ok) {
        setMsg(card, "err", "Erro ao salvar: " + (data.error || "erro desconhecido"));
        return;
      }

      setMsg(card, "ok", naoAprovado ? "Justificativa salva com sucesso!" : "Avaliação salva com sucesso!");
    } catch (err) {
      setMsg(card, "err", "Erro de conexão ao salvar.");
    } finally {
      btn.disabled = false;
      btn.textContent = oldText;
    }
  });

  applyFilters();
});
