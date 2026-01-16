(function () {
  const select = document.getElementById("tipo_exame");
  const blocks = document.querySelectorAll(".type-block");

  function updateBlocks() {
    const value = select.value;
    blocks.forEach((b) => {
      const type = b.getAttribute("data-type");
      b.hidden = type !== value;
    });

    // (opcional) você pode ajustar required dinamicamente quando evoluir os outros tipos
  }

  select.addEventListener("change", updateBlocks);
  updateBlocks();
})();
