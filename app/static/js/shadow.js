// Comportamentos pequenos da interface. Sem dependências externas.
document.addEventListener("DOMContentLoaded", () => {
  // Menu lateral no celular
  const sidebar = document.getElementById("sidebar");
  document.querySelectorAll("[data-toggle-sidebar]").forEach((button) => {
    button.addEventListener("click", () => sidebar.classList.toggle("is-open"));
  });

  // Mensagens do sistema somem depois de alguns segundos
  document.querySelectorAll(".flash").forEach((flash) => {
    setTimeout(() => flash.classList.add("is-hidden"), 6000);
  });

  // Filtros que enviam o formulário ao mudar (evita JS inline, bloqueado pela CSP)
  document.querySelectorAll("[data-autosubmit]").forEach((input) => {
    input.addEventListener("change", () => input.form.submit());
  });

  // Abre/fecha painéis com data-toggle="id-do-alvo" (formulários recolhíveis)
  document.querySelectorAll("[data-toggle]").forEach((button) => {
    const target = document.getElementById(button.dataset.toggle);
    if (!target) return;
    button.addEventListener("click", () => target.classList.toggle("is-collapsed"));
  });
});
