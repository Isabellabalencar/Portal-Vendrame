document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("tipo_exame");
  const blocks = document.querySelectorAll(".type-block");
  const form = document.querySelector("form");

  // =====================================
  // Remove mensagem de sucesso antiga
  // =====================================
  function clearOldSuccess() {
    document.querySelectorAll(".alert-success, .flash-success, .success").forEach((el) => el.remove());
  }

  document.querySelectorAll("input, select, textarea").forEach((el) => {
    el.addEventListener("change", clearOldSuccess);
    el.addEventListener("input", clearOldSuccess);
  });

  // =====================================
  // Ativa/Desativa campos por bloco
  // =====================================
  function setActive(container, isActive) {
    const fields = container.querySelectorAll(
      'input:not([type="submit"]):not([type="radio"]), select, textarea'
    );

    fields.forEach((el) => {
      el.disabled = !isActive;

      // Avaliação médica é controlada no toggle interno
      if (el.id === "am_justificativa" || el.id === "am_pdf") {
        if (!isActive) el.required = false;
        return;
      }

      // file input: não forçar required aqui
      if (el.type === "file") {
        if (!isActive) el.required = false;
        return;
      }

      if (!isActive) {
        el.required = false;
        return;
      }

      const id = el.id;
      if (!id) return;

      const label = container.querySelector(`label[for="${CSS.escape(id)}"]`);
      const isRequiredByUI = !!(label && label.querySelector(".req"));
      el.required = isRequiredByUI;
    });
  }

  function toggleBlocks() {
    const tipo = select.value;

    blocks.forEach((block) => {
      const isActive = block.dataset.type === tipo;
      block.hidden = !isActive;
      setActive(block, isActive);
    });

    // ao trocar o tipo, garante que o toggle da avaliação médica re-aplique corretamente
    safeApplyAvaliacaoMedica();
  }

  // =====================================
  // Avaliação Médica: toggle (texto x pdf)
  // =====================================
  const radios = document.querySelectorAll('input[name="am_forma"]');
  const boxTexto = document.querySelector('.am-text[data-am="texto"]');
  const boxPdf = document.querySelector('.am-pdf[data-am="pdf"]');
  const txt = document.getElementById("am_justificativa");
  const amPdf = document.getElementById("am_pdf");

  function isAvaliacaoAtiva() {
    return (select?.value || "") === "Avaliação médica";
  }

  function applyAvaliacaoMedica() {
    const modo = document.querySelector('input[name="am_forma"]:checked')?.value || "";
    const isTexto = modo === "texto";
    const isPdf = modo === "pdf";

    if (boxTexto) boxTexto.hidden = !isTexto;
    if (boxPdf) boxPdf.hidden = !isPdf;

    if (txt) {
      txt.disabled = !isTexto;
      txt.required = isTexto;
      if (!isTexto) txt.value = "";
    }

    if (amPdf) {
      amPdf.disabled = !isPdf;
      amPdf.required = isPdf;
      if (!isPdf) amPdf.value = "";
    }
  }

  function safeApplyAvaliacaoMedica() {
    if (!isAvaliacaoAtiva()) {
      if (txt) { txt.required = false; txt.disabled = true; }
      if (amPdf) { amPdf.required = false; amPdf.disabled = true; }
      if (boxTexto) boxTexto.hidden = true;
      if (boxPdf) boxPdf.hidden = true;
      return;
    }
    applyAvaliacaoMedica();
  }

  radios.forEach((r) => r.addEventListener("change", safeApplyAvaliacaoMedica));

  // =====================================
  // Bloqueia SUBMIT se marcou PDF e não anexou
  // =====================================
  if (form) {
    form.addEventListener("submit", (e) => {
      if (!isAvaliacaoAtiva()) return;

      const modo = document.querySelector('input[name="am_forma"]:checked')?.value || "";
      if (modo === "pdf") {
        const temArquivo = amPdf && amPdf.files && amPdf.files.length > 0;
        if (!temArquivo) {
          e.preventDefault();
          alert("❌ Para 'Anexo em PDF', você precisa anexar um arquivo PDF.");
          if (amPdf) amPdf.focus();
          return;
        }
      }
    });
  }

  // init
  toggleBlocks();
  select.addEventListener("change", toggleBlocks);
  safeApplyAvaliacaoMedica();
});
