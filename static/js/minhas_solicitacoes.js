document.addEventListener("DOMContentLoaded", () => {
  const q = document.getElementById("q");
  const fTipo = document.getElementById("f_tipo");
  const fProto = document.getElementById("f_protocolo");
  const fStatus = document.getElementById("f_status");

  const list = document.getElementById("list");
  if (!list) return;

  const cards = Array.from(list.querySelectorAll(".req-card"));
  const emptyState = document.getElementById("emptyState") || list.querySelector(".empty-state");

  // ===== helpers =====
  const normText = (v) =>
    (v ?? "")
      .toString()
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, ""); // remove acentos

  const onlyDigits = (v) => (v ?? "").toString().replace(/\D+/g, "");
  const isAll = (v) => {
    const x = normText(v);
    return x === "" || x === "todos";
  };

  function setEmpty(show) {
    if (!emptyState) return;
    emptyState.style.display = show ? "block" : "none";
  }

  // ===== indexa cada card uma vez (inclui texto do card inteiro, mesmo hidden) =====
  const index = new Map();
  cards.forEach((card) => {
    const user = card.dataset.user || "";
    const cpf = card.dataset.cpf || "";
    const proto = card.dataset.proto || "";
    const fullText = card.textContent || ""; // inclui conteúdo do body mesmo fechado

    index.set(card, {
      text: normText(`${user} ${cpf} ${proto} ${fullText}`),
      digits: onlyDigits(`${cpf} ${fullText}`),
    });
  });

  function applyFilters() {
    const termRaw = normText(q?.value);
    const termDigits = onlyDigits(q?.value);

    const tipo = normText(fTipo?.value);
    const proto = normText(fProto?.value);
    const status = normText(fStatus?.value);

    let visible = 0;

    cards.forEach((card) => {
      const i = index.get(card);

      // busca por nome/cpf (e agora também acha mesmo com acento/fechado)
      let okSearch = true;
      if (termRaw) {
        // se usuário digitou número, prioriza busca por dígitos (CPF)
        if (termDigits) okSearch = i.digits.includes(termDigits);
        else okSearch = i.text.includes(termRaw);
      }

      // filtros por dataset
      const cardTipo = normText(card.dataset.tipo);
      const cardProto = normText(card.dataset.proto);
      const cardStatus = normText(card.dataset.status);

      const okTipo = isAll(tipo) || cardTipo === tipo;
      const okProto = isAll(proto) || cardProto === proto;
      const okStatus = isAll(status) || cardStatus === status;

      const show = okSearch && okTipo && okProto && okStatus;
      card.style.display = show ? "" : "none";
      if (show) visible += 1;
    });

    setEmpty(visible === 0);
  }

  // ===== eventos =====
  q?.addEventListener("input", applyFilters);
  fTipo?.addEventListener("change", applyFilters);
  fProto?.addEventListener("change", applyFilters);
  fStatus?.addEventListener("change", applyFilters);

  // toggle detalhes
  list.addEventListener("click", (e) => {
    const btn = e.target.closest(".toggle");
    if (!btn) return;

    const card = btn.closest(".req-card");
    if (!card) return;

    const body = card.querySelector(".req-body");
    if (!body) return;

    const expanded = btn.getAttribute("aria-expanded") === "true";
    btn.setAttribute("aria-expanded", expanded ? "false" : "true");
    body.hidden = expanded;
  });

  applyFilters();
});
