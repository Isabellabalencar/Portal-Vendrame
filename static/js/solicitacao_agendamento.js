document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("tipo_exame");
  const blocks = document.querySelectorAll(".type-block");
  const form = document.querySelector("form");

  // =====================================
  // Normaliza string (remove acentos) -> evita erro com "Avaliação médica" vs "avaliacao medica"
  // =====================================
  function normalize(s) {
    return (s || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  // =====================================
  // Remove SOMENTE mensagem de sucesso antiga (não remove erro)
  // =====================================
  function clearOldSuccess() {
    document
      .querySelectorAll(".alert.alert-success, .alert-success, .flash-success")
      .forEach((el) => el.remove());
  }

  document.querySelectorAll("input, select, textarea").forEach((el) => {
    el.addEventListener("change", clearOldSuccess);
    el.addEventListener("input", clearOldSuccess);
  });

  // =====================================
  // Mostra nome do arquivo selecionado (genérico)
  // - Você precisa ter no HTML um elemento (ex.: <small id="am_pdf_name"></small>)
  // - Mesma lógica para Retorno ao Trabalho (ex.: <small id="rt_pdf_name"></small>)
  // =====================================
  function bindFileName(inputId, outputId, prefix = "Arquivo selecionado: ") {
    const input = document.getElementById(inputId);
    const out = document.getElementById(outputId);

    if (!input || !out) return;

    const update = () => {
      const file = input.files && input.files.length > 0 ? input.files[0] : null;
      out.textContent = file ? `${prefix}${file.name}` : "";
    };

    input.addEventListener("change", update);
    update();

    // devolve helpers para limpar quando você zerar o input
    return {
      clear: () => (out.textContent = ""),
      update,
    };
  }

  // IDs esperados:
  // - Avaliação Médica: input#am_pdf e output#am_pdf_name
  // - Retorno ao Trabalho: input#rt_pdf e output#rt_pdf_name (se o seu id for diferente, troque aqui)
  const amFileUI = bindFileName("am_pdf", "am_pdf_name");
  const rtFileUI = bindFileName("rt_pdf", "rt_pdf_name");

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
        if (!isActive) {
          el.required = false;
          if (el.id === "am_pdf") {
            el.value = "";
            amFileUI?.clear?.();
          }
        }
        return;
      }

      // Retorno ao Trabalho: se seu input de arquivo for rt_pdf, limpa ao desativar
      if (el.id === "rt_pdf") {
        if (!isActive) {
          el.required = false;
          el.value = "";
          rtFileUI?.clear?.();
        }
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
    const tipo = select?.value || "";

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
    // robusto contra acento/maiúscula
    return normalize(select?.value) === "avaliacao medica";
  }

  function applyAvaliacaoMedica() {
    const modo =
      document.querySelector('input[name="am_forma"]:checked')?.value || "";
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

      // se não for PDF, limpa o arquivo e também o nome exibido
      if (!isPdf) {
        amPdf.value = "";
        amFileUI?.clear?.();
      } else {
        // se for PDF, atualiza o label (caso algo já esteja selecionado)
        amFileUI?.update?.();
      }
    }
  }

  function safeApplyAvaliacaoMedica() {
    if (!isAvaliacaoAtiva()) {
      if (txt) {
        txt.required = false;
        txt.disabled = true;
      }
      if (amPdf) {
        amPdf.required = false;
        amPdf.disabled = true;
        amPdf.value = "";
        amFileUI?.clear?.();
      }
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

      const modo =
        document.querySelector('input[name="am_forma"]:checked')?.value || "";

      if (modo === "pdf") {
        const temArquivo = amPdf && amPdf.files && amPdf.files.length > 0;

        if (!temArquivo) {
          e.preventDefault();
          alert("❌ Para 'Anexo em PDF', você precisa anexar um arquivo PDF.");
          amPdf?.focus();
          return;
        }

        // valida extensão no client-side também (opcional, mas ajuda)
        const fileName = (amPdf.files[0]?.name || "").toLowerCase();
        if (fileName && !fileName.endsWith(".pdf")) {
          e.preventDefault();
          alert("❌ O anexo precisa ser um PDF.");
          amPdf?.focus();
          return;
        }
      }
    });
  }

  // init
  toggleBlocks();
  select?.addEventListener("change", toggleBlocks);
  safeApplyAvaliacaoMedica();
});


document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("r_pdf");
  const nameBox = document.getElementById("r_pdf_name");

  if (!input || !nameBox) return;

  function updateFileName() {
    const file = input.files && input.files.length > 0 ? input.files[0] : null;
    nameBox.textContent = file ? file.name : "Nenhum arquivo escolhido";
  }

  input.addEventListener("change", updateFileName);

  // garante estado inicial
  updateFileName();
});
