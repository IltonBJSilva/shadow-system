// Comportamentos pequenos da interface. Sem dependências externas além do Turbo (navegação sem recarregar).
// initPage roda a cada página: na primeira carga e em cada navegação do Turbo (turbo:load).
function initPage() {
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

  // Controles de áudio (menu lateral e Configurações) mostram o estado atual.
  renderAudioControls();

  // Filtros que enviam o formulário ao mudar (evita JS inline, bloqueado pela CSP)
  document.querySelectorAll("[data-autosubmit]").forEach((input) => {
    input.addEventListener("change", () => (input.form.requestSubmit ? input.form.requestSubmit() : input.form.submit()));
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
}

document.addEventListener("turbo:load", initPage);
document.addEventListener("DOMContentLoaded", () => { if (!window.Turbo) initPage(); });

// ---------- Áudio: botões [data-audio-toggle="music|sfx|entrance"] e controles [data-audio-pref] ----------
const AUDIO_LABELS = {
  music: ["♫ Música ligada", "♫ Música desligada"],
  sfx: ["🔊 Efeitos ligados", "🔇 Efeitos desligados"],
  entrance: ["Voz de entrada ligada", "Voz de entrada desligada"],
};

function renderAudioControls() {
  if (!window.ShadowAudio) return;
  const prefs = window.ShadowAudio.prefs();
  document.querySelectorAll("[data-audio-toggle]").forEach((button) => {
    const name = button.dataset.audioToggle;
    const labels = AUDIO_LABELS[name];
    button.setAttribute("aria-pressed", prefs[name] ? "true" : "false");
    if (labels && !button.dataset.keepLabel) button.textContent = prefs[name] ? labels[0] : labels[1];
  });
  document.querySelectorAll("[data-audio-pref]").forEach((input) => {
    const value = prefs[input.dataset.audioPref];
    if (input.type === "checkbox") input.checked = Boolean(value);
    else input.value = Math.round(value * 100);
    const output = input.closest(".field") && input.closest(".field").querySelector("[data-audio-value]");
    if (output) output.textContent = `${Math.round(value * 100)}%`;
  });
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-audio-toggle]");
  if (!button || !window.ShadowAudio) return;
  const name = button.dataset.audioToggle;
  window.ShadowAudio.setPref(name, !window.ShadowAudio.prefs()[name]);
  if (name === "sfx" && window.ShadowAudio.prefs().sfx) window.ShadowAudio.play("notify");
});

document.addEventListener("input", (event) => {
  const input = event.target.closest("[data-audio-pref]");
  if (!input || !window.ShadowAudio) return;
  window.ShadowAudio.setPref(input.dataset.audioPref, input.type === "checkbox" ? input.checked : Number(input.value) / 100);
});

document.addEventListener("change", (event) => {
  const input = event.target.closest('[data-audio-pref="sfxVolume"]');
  if (input && window.ShadowAudio) window.ShadowAudio.play("notify"); // amostra do novo volume
});

document.addEventListener("shadow:audio-prefs", renderAudioControls);

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-audio-test]");
  if (button && window.ShadowAudio) window.ShadowAudio.play(button.dataset.audioTest);
});

// Copiar link (convites): botão [data-copy] copia o campo [data-copy-source] do mesmo bloco.
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-copy]");
  if (!button) return;
  const box = button.closest("[data-copy-box]") || document;
  const source = box.querySelector("[data-copy-source]");
  if (!source) return;
  const done = () => { button.textContent = "Copiado!"; setTimeout(() => { button.textContent = "Copiar link"; }, 2000); };
  if (navigator.clipboard) navigator.clipboard.writeText(source.value).then(done, () => { source.select(); });
  else { source.select(); document.execCommand("copy"); done(); }
});

// Ações destrutivas: <form data-confirm="pergunta"> pede confirmação antes de enviar.
document.addEventListener("submit", (event) => {
  const form = event.target.closest("form[data-confirm]");
  if (form && !window.confirm(form.dataset.confirm)) {
    event.preventDefault();
    event.stopImmediatePropagation();
  }
}, true);

// Formulários demorados (IA): desliga o botão e mostra que está trabalhando, sem envio duplo.
document.addEventListener("submit", (event) => {
  const form = event.target.closest("[data-busy-form], form");
  if (!form) return;
  form.querySelectorAll("[data-busy-label]").forEach((button) => {
    button.disabled = true;
    button.textContent = button.dataset.busyLabel;
    button.classList.add("is-busy");
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
