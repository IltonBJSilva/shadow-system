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
    success: "quest", levelup: "levelup", achievement: "achievement", bonus: "bonus", penalty: "penalty",
    error: "error", info: "notify",
  };
  const priority = ["levelup", "achievement", "penalty", "bonus", "success", "error", "info"];
  const categories = flashes.map((f) => f.dataset.category);
  const top = priority.find((c) => categories.includes(c));
  if (top && window.ShadowSound) {
    const playIt = () => window.ShadowSound.play(SOUND_BY_CATEGORY[top]);
    playIt();
    document.addEventListener("pointerdown", playIt, { once: true });
    setTimeout(() => document.removeEventListener("pointerdown", playIt), 4000);
  }
  showLevelUp(flashes);
  flashes.forEach((flash) => {
    const sticky = ["levelup", "penalty", "achievement"].includes(flash.dataset.category);
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

  // Seleção em massa: caixas [data-bulk-item] ligadas a um <form data-bulk> pelo atributo form=
  document.querySelectorAll("form[data-bulk]").forEach((bulk) => {
    const items = () => Array.from(document.querySelectorAll(`[data-bulk-item][form="${bulk.id}"]`));
    const all = bulk.querySelector("[data-bulk-all]");
    const count = bulk.querySelector("[data-bulk-count]");
    const refresh = () => {
      const checked = items().filter((item) => item.checked).length;
      if (count) count.textContent = `${checked} selecionada(s)`;
      bulk.querySelectorAll("[data-bulk-action]").forEach((button) => { button.disabled = checked === 0; });
      if (all) {
        all.checked = checked > 0 && checked === items().length;
        all.indeterminate = checked > 0 && checked < items().length;
      }
    };
    if (all) all.addEventListener("change", () => { items().forEach((item) => { item.checked = all.checked; }); refresh(); });
    items().forEach((item) => item.addEventListener("change", refresh));
    refresh();
  });
});

// Janela de LEVEL UP: aparece por cima de tudo quando uma mensagem de subida de nível chega.
// Some sozinha em ~3,5 s, com clique ou Esc. Respeita "reduzir movimento".
function showLevelUp(flashes) {
  const levelFlash = flashes.find((f) => f.dataset.category === "levelup" && /LEVEL UP/i.test(f.textContent));
  if (!levelFlash) return;
  const level = (levelFlash.textContent.match(/n[ií]vel (\d+)/i) || [])[1];
  const rankFlash = flashes.find((f) => f.dataset.category === "levelup" && /rank/i.test(f.textContent));
  const rank = rankFlash ? rankFlash.textContent.replace(/^.*rank desbloqueado:\s*/i, "").replace(/\.$/, "").trim() : "";
  const overlay = document.createElement("div");
  overlay.className = "levelup-overlay";
  overlay.setAttribute("role", "alertdialog");
  overlay.setAttribute("aria-label", "Level up");
  overlay.innerHTML = `
    <div class="levelup-card">
      <p class="levelup-tag">[SYSTEM]</p>
      <p class="levelup-title">LEVEL UP!</p>
      <p class="levelup-line">VOCÊ EVOLUIU.</p>
      ${level ? `<p class="levelup-level"><span>NÍVEL</span> ${level}</p>` : ""}
      <p class="levelup-line small">NOVO NÍVEL DESBLOQUEADO${rank ? ` · RANK ${escapeHtml(rank)}` : ""}</p>
    </div>`;
  document.body.appendChild(overlay);
  const close = () => {
    overlay.classList.add("is-leaving");
    setTimeout(() => overlay.remove(), 400);
    document.removeEventListener("keydown", onKey);
  };
  const onKey = (event) => { if (event.key === "Escape" || event.key === "Enter") close(); };
  overlay.addEventListener("click", close);
  document.addEventListener("keydown", onKey);
  setTimeout(close, 3600);
}

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
