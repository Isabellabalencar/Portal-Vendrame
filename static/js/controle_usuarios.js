document.addEventListener("DOMContentLoaded", () => {
  // ========= HELPERS =========
  const select = document.getElementById("acao");
  const blocks = document.querySelectorAll(".form-block");

  function showForm(value) {
    blocks.forEach((b) => {
      b.hidden = b.dataset.form !== value;
    });

    // ✅ quando selecionar "list", carrega do backend
    if (value === "list") {
      loadUsers();
    }
  }

  // ========= LISTAR USUÁRIOS (fetch rota nova) =========
  async function loadUsers() {
    const tbody = document.getElementById("usersTbody");
    if (!tbody) return;

    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="empty">Carregando...</td>
      </tr>
    `;

    try {
      const res = await fetch("/admin/usuarios/listar", {
        method: "GET",
        credentials: "same-origin",
        headers: { "Accept": "application/json" },
      });

      if (!res.ok) throw new Error("Falha ao buscar usuários");

      const usuarios = await res.json();

      if (!Array.isArray(usuarios) || usuarios.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="empty">Nenhum usuário encontrado.</td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = "";

      usuarios.forEach((u, idx) => {
        const tr = document.createElement("tr");
        const tipo = (u.type || "").toLowerCase();

        tr.innerHTML = `
          <td class="col-id">${idx + 1}</td>
          <td class="strong">${u.user || ""}</td>
          <td>${u.email || ""}</td>
          <td>${u.name || ""}</td>
          <td class="col-type">
            <span class="badge badge-${tipo}">${tipo}</span>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="empty">Erro ao carregar usuários.</td>
        </tr>
      `;
    }
  }

  // ========= TROCA DE FORM PELO DROPDOWN =========
  if (select && blocks.length) {
    showForm(select.value || "add");

    select.addEventListener("change", (e) => {
      showForm(e.target.value);
    });
  }

  // ========= OLHO DA SENHA (suporta múltiplos campos) =========
  function bindEyeButtons() {
    const eyeButtons = document.querySelectorAll("#toggleEye, [data-toggle-eye]");

    eyeButtons.forEach((btn) => {
      // evita duplicar listener
      if (btn.dataset.bound === "1") return;
      btn.dataset.bound = "1";

      btn.addEventListener("click", () => {
        const wrap = btn.closest(".password-wrap");
        if (!wrap) return;

        const input = wrap.querySelector('input[type="password"], input[type="text"]');
        if (!input) return;

        const isPass = input.type === "password";
        input.type = isPass ? "text" : "password";

        const openIcon = btn.querySelector(".eye-open");
        const closedIcon = btn.querySelector(".eye-closed");

        if (openIcon && closedIcon) {
          openIcon.style.display = isPass ? "none" : "block";
          closedIcon.style.display = isPass ? "block" : "none";
        }

        btn.setAttribute("aria-label", isPass ? "Ocultar senha" : "Mostrar senha");
        btn.setAttribute("aria-pressed", isPass ? "true" : "false");
      });
    });
  }

  bindEyeButtons();
});
