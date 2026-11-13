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

  // Pré-visualização de imagens selecionadas no Buffer (postagens)
  initBufferImagePreviews();
}

function initBufferImagePreviews() {
  const input = document.getElementById("buffer-images-input");
  const container = document.getElementById("buffer-preview-container");
  const grid = document.getElementById("buffer-preview-grid");
  const countLabel = document.getElementById("buffer-preview-count");
  const clearBtn = document.getElementById("buffer-preview-clear");
  if (!input || !container || !grid) return;

  const renderPreviews = () => {
    grid.innerHTML = "";
    const files = Array.from(input.files || []).slice(0, 10);
    if (!files.length) {
      container.style.display = "none";
      return;
    }
    container.style.display = "block";
    if (countLabel) {
      countLabel.textContent = `${files.length} mídia(s) selecionada(s)`;
    }
    files.forEach((file, index) => {
      const card = document.createElement("div");
      card.className = "buffer-preview-card";

      const badge = document.createElement("span");
      badge.className = "buffer-preview-badge";
      const isVideo = file.type.startsWith("video/") || /\.(mp4|mov|webm|m4v)$/i.test(file.name);
      badge.textContent = isVideo ? "▶ Vídeo" : (index === 0 ? "1ª (Capa)" : `${index + 1}ª`);

      let mediaEl;
      if (isVideo) {
        mediaEl = document.createElement("video");
        mediaEl.className = "buffer-preview-img";
        mediaEl.src = URL.createObjectURL(file) + "#t=0.5";
        mediaEl.muted = true;
        mediaEl.playsInline = true;
        mediaEl.preload = "metadata";
      } else {
        mediaEl = document.createElement("img");
        mediaEl.className = "buffer-preview-img";
        mediaEl.src = URL.createObjectURL(file);
        mediaEl.alt = file.name;
      }

      const name = document.createElement("span");
      name.className = "buffer-preview-name";
      name.textContent = file.name;
      name.title = file.name;

      card.appendChild(badge);
      card.appendChild(mediaEl);
      card.appendChild(name);
      grid.appendChild(card);
    });
  };

  input.addEventListener("change", renderPreviews);
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      input.value = "";
      renderPreviews();
    });
  }
}

// ---------- Modal de pré-visualização de vídeos e imagens no Buffer ----------
(function initBufferMediaModal() {
  let modal = null;
  let titleEl = null;
  let bodyEl = null;
  let captionEl = null;

  const ensureModal = () => {
    if (modal && document.body.contains(modal)) return;
    modal = document.createElement("div");
    modal.className = "buffer-media-modal";
    modal.hidden = true;
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.innerHTML = `
      <div class="buffer-media-modal-card">
        <div class="buffer-media-modal-head">
          <span class="buffer-media-modal-title"></span>
          <button type="button" class="btn btn-sm btn-ghost" data-media-close>✕ Fechar</button>
        </div>
        <div class="buffer-media-modal-body"></div>
        <div class="buffer-media-modal-caption"></div>
      </div>`;
    document.body.appendChild(modal);
    titleEl = modal.querySelector(".buffer-media-modal-title");
    bodyEl = modal.querySelector(".buffer-media-modal-body");
    captionEl = modal.querySelector(".buffer-media-modal-caption");
  };

  const closeModal = () => {
    if (!modal || modal.hidden) return;
    const vid = bodyEl && bodyEl.querySelector("video");
    if (vid) {
      vid.pause();
      vid.removeAttribute("src");
      vid.load();
    }
    if (bodyEl) bodyEl.innerHTML = "";
    modal.hidden = true;
  };

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-media-preview]");
    if (trigger) {
      ensureModal();
      const url = trigger.dataset.mediaUrl || "";
      const type = trigger.dataset.mediaType || "image";
      const title = trigger.dataset.mediaTitle || "Pré-visualização";
      const text = trigger.dataset.mediaText || "";

      titleEl.textContent = title;
      bodyEl.innerHTML = "";
      if (type === "video") {
        const video = document.createElement("video");
        video.src = url;
        video.controls = true;
        video.autoplay = true;
        video.playsInline = true;
        video.preload = "auto";
        bodyEl.appendChild(video);
      } else {
        const img = document.createElement("img");
        img.src = url;
        img.alt = title;
        bodyEl.appendChild(img);
      }
      captionEl.textContent = text;
      captionEl.hidden = !text;
      modal.hidden = false;
      return;
    }
    if (modal && !modal.hidden) {
      if (event.target === modal || event.target.closest("[data-media-close]")) {
        closeModal();
      }
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeModal();
  });
})();

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


// ---------- App instalável (PWA) ----------
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => { navigator.serviceWorker.register("/sw.js").catch(() => {}); });
}
let installPrompt = null;
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  document.querySelectorAll("[data-install]").forEach((button) => { button.hidden = false; });
});
document.addEventListener("turbo:load", () => {
  if (installPrompt) document.querySelectorAll("[data-install]").forEach((button) => { button.hidden = false; });
});
document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-install]");
  if (!button || !installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt = null;
  document.querySelectorAll("[data-install]").forEach((b) => { b.hidden = true; });
});


// ---------- Comando de voz (Arquiteto): [data-voice-for="id-do-campo"] ----------
// Usa o reconhecimento de fala do navegador (Web Speech API). Só aparece onde o navegador suporta.
const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition;
document.addEventListener("turbo:load", () => {
  if (!SpeechRecognitionApi) return;
  document.querySelectorAll("[data-voice-for], [data-voice-note]").forEach((el) => { el.hidden = false; });
});
let listening = null;
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-voice-for]");
  if (!button || !SpeechRecognitionApi) return;
  const field = document.getElementById(button.dataset.voiceFor);
  if (!field) return;
  if (listening) { listening.stop(); return; }
  const recognition = new SpeechRecognitionApi();
  recognition.lang = "pt-BR";
  recognition.interimResults = true;
  const before = field.value ? field.value.trim() + " " : "";
  const label = button.textContent;
  recognition.onresult = (e) => {
    field.value = before + Array.from(e.results).map((r) => r[0].transcript).join(" ");
  };
  recognition.onend = () => { listening = null; button.textContent = label; button.classList.remove("is-busy"); field.focus(); };
  recognition.onerror = () => { recognition.stop(); };
  listening = recognition;
  button.textContent = "● Ouvindo... (toque para parar)";
  button.classList.add("is-busy");
  if (window.ShadowAudio) window.ShadowAudio.play("open");
  recognition.start();
});
