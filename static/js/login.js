document.addEventListener("DOMContentLoaded", () => {
  const inputSenha = document.getElementById("senha");
  const btnToggle = document.getElementById("toggleEye");

  // Só roda se existir na página
  if (!inputSenha || !btnToggle) return;

  function togglePassword() {
    const isHidden = inputSenha.type === "password";
    inputSenha.type = isHidden ? "text" : "password";
    btnToggle.classList.toggle("password-visible", isHidden);
    btnToggle.setAttribute("aria-label", isHidden ? "Ocultar senha" : "Mostrar senha");
    btnToggle.setAttribute("aria-pressed", String(isHidden));
  }

  btnToggle.addEventListener("click", togglePassword);
  btnToggle.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      togglePassword();
    }
  });
});
