// Comportamentos pequenos da interface. Sem dependências externas.
document.addEventListener("DOMContentLoaded", () => {
  // Menu lateral no celular
  const sidebar = document.getElementById("sidebar");
  document.querySelectorAll("[data-toggle-sidebar]").forEach((button) => {
    button.addEventListener("click", () => sidebar.classList.toggle("is-open"));
  });

  // Mensagens do sistema: tocam o som da categoria e somem depois de alguns segundos.
  // O navegador só libera áudio depois de uma interação; como as mensagens aparecem logo após um
  // clique (concluir quest, marcar hábito), normalmente toca. Se não tocar, toca no próximo clique.
  const flashes = Array.from(document.querySelectorAll(".flash"));
  const SOUND_BY_CATEGORY = {
    success: "quest", levelup: "levelup", bonus: "bonus", penalty: "penalty", error: "error", info: "notify",
  };
  const priority = ["levelup", "penalty", "bonus", "success", "error", "info"];
  const categories = flashes.map((f) => f.dataset.category);
  const top = priority.find((c) => categories.includes(c));
  if (top && window.ShadowSound) {
    const playIt = () => window.ShadowSound.play(SOUND_BY_CATEGORY[top]);
    playIt();
    document.addEventListener("pointerdown", playIt, { once: true });
    setTimeout(() => document.removeEventListener("pointerdown", playIt), 4000);
  }
  flashes.forEach((flash) => {
    const sticky = ["levelup", "penalty"].includes(flash.dataset.category);
    setTimeout(() => flash.classList.add("is-hidden"), sticky ? 9000 : 6000);
    flash.addEventListener("click", () => flash.classList.add("is-hidden"));
  });

  // Botão de som liga/desliga
  const soundToggle = document.querySelector("[data-sound-toggle]");
  if (soundToggle && window.ShadowSound) {
    const render = () => { soundToggle.textContent = window.ShadowSound.enabled() ? "🔊 Som ligado" : "🔇 Som desligado"; };
    render();
    soundToggle.addEventListener("click", () => {
      window.ShadowSound.setEnabled(!window.ShadowSound.enabled());
      render();
      window.ShadowSound.play("notify");
    });
  }

  // Filtros que enviam o formulário ao mudar (evita JS inline, bloqueado pela CSP)
  document.querySelectorAll("[data-autosubmit]").forEach((input) => {
    input.addEventListener("change", () => input.form.submit());
  });

  // Abre/fecha painéis com data-toggle="id-do-alvo" (formulários recolhíveis)
  document.querySelectorAll("[data-toggle]").forEach((button) => {
    const target = document.getElementById(button.dataset.toggle);
    if (!target) return;
    button.addEventListener("click", () => {
      target.classList.toggle("is-collapsed");
      if (window.ShadowSound) window.ShadowSound.play("notify");
    });
  });
});
