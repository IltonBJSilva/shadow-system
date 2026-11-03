// Áudio do System: um só lugar para música de fundo, vozes (entrada, level up, conquista, Zona de Falha)
// e efeitos sintetizados.
//
// - Efeitos curtos (quest, bônus, erro, notificação...) são sintetizados na hora com a Web Audio API:
//   tons originais, sem arquivo.
// - Música e vozes são arquivos enviados pelo dono em Configurações > Mídias do System (servidos em
//   /media/<slot>). Sem arquivo, cada momento usa o efeito sintetizado e nada quebra.
// - A navegação entre páginas não recarrega a janela (Turbo), então a música segue tocando. Num
//   recarregamento completo, ela continua do ponto em que parou (sessionStorage).
// - Navegadores só liberam som depois de uma interação: o que for bloqueado toca no primeiro toque/tecla.
//
// Uso: ShadowSound.play("quest" | "levelup" | "penalty" | "error" | "notify" | "bonus" | "boot" | "activate"
//        | "achievement" | "open")
//      ShadowAudio.prefs() / ShadowAudio.setPref("music" | "musicVolume" | "sfx" | "sfxVolume" | "entrance", valor)
// Preferências ficam no navegador (localStorage "shadow.audio"), por aparelho.
(function () {
  const PREFS_KEY = "shadow.audio";
  const LEGACY_KEY = "shadow.sound";
  const ENTRANCE_KEY = "shadow.entrance";
  const MUSIC_POS_KEY = "shadow.music.pos";
  const DEFAULTS = { music: true, musicVolume: 0.35, sfx: true, sfxVolume: 0.8, entrance: true };
  const VOICE_SLOTS = ["levelup", "achievement", "penalty"];

  // ---------- Preferências ----------
  function storage(kind) {
    try { return window[kind]; } catch (e) { return null; }
  }

  function prefs() {
    const saved = {};
    try { Object.assign(saved, JSON.parse(storage("localStorage").getItem(PREFS_KEY) || "{}")); } catch (e) { /* sem storage */ }
    try {
      if (!("sfx" in saved) && storage("localStorage").getItem(LEGACY_KEY) === "off") saved.sfx = false;
    } catch (e) { /* sem storage */ }
    return Object.assign({}, DEFAULTS, saved);
  }

  function setPref(name, value) {
    if (!(name in DEFAULTS)) return;
    const next = prefs();
    next[name] = typeof DEFAULTS[name] === "number" ? Math.min(1, Math.max(0, Number(value) || 0)) : Boolean(value);
    try { storage("localStorage").setItem(PREFS_KEY, JSON.stringify(next)); } catch (e) { /* sem storage */ }
    applyPrefs(next);
    document.dispatchEvent(new CustomEvent("shadow:audio-prefs", { detail: next }));
  }

  // ---------- Mídias disponíveis (o servidor informa a versão de cada slot) ----------
  function mediaVersions() {
    const meta = document.querySelector('meta[name="shadow-media"]');
    try { return JSON.parse((meta && meta.content) || "{}"); } catch (e) { return {}; }
  }

  function mediaUrl(slot) {
    const v = mediaVersions()[slot];
    return v ? `/media/${slot}?v=${v}` : null;
  }

  function inExperience() {
    return document.body && document.body.dataset.experience === "main";
  }

  // ---------- Web Audio (efeitos sintetizados e volume no iPhone) ----------
  let ctx = null;
  let sfxBus = null;

  function audio() {
    if (!ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      ctx = new AudioCtx();
      sfxBus = ctx.createGain();
      sfxBus.gain.value = prefs().sfxVolume;
      sfxBus.connect(ctx.destination);
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  // No iPhone/iPad o volume de <audio> é só leitura: lá o volume passa por um GainNode.
  const nativeVolume = (() => {
    try { const a = new Audio(); a.volume = 0.5; return Math.abs(a.volume - 0.5) < 0.01; } catch (e) { return true; }
  })();

  function routed(el) {
    if (nativeVolume || el._gain) return el;
    const ac = audio();
    if (!ac) return el;
    try {
      const source = ac.createMediaElementSource(el);
      el._gain = ac.createGain();
      source.connect(el._gain);
      el._gain.connect(ac.destination);
    } catch (e) { /* já ligado ou sem suporte: segue com o volume nativo */ }
    return el;
  }

  function setVolume(el, value) {
    if (!el) return;
    if (el._gain) el._gain.gain.value = value;
    else el.volume = value;
  }

  // Um tom com envelope (ataque rápido, decaimento suave) e eco leve.
  function tone(ac, { freq, start = 0, duration = 0.18, type = "sine", gain = 0.18, slideTo = null, echo = true }) {
    const t0 = ac.currentTime + start;
    const osc = ac.createOscillator();
    const amp = ac.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t0);
    if (slideTo) osc.frequency.exponentialRampToValueAtTime(slideTo, t0 + duration);
    amp.gain.setValueAtTime(0.0001, t0);
    amp.gain.exponentialRampToValueAtTime(gain, t0 + 0.012);
    amp.gain.exponentialRampToValueAtTime(0.0001, t0 + duration);
    osc.connect(amp);
    amp.connect(sfxBus);
    if (echo) {
      const delay = ac.createDelay();
      const feedback = ac.createGain();
      delay.delayTime.value = 0.11;
      feedback.gain.value = 0.28;
      amp.connect(delay);
      delay.connect(feedback);
      feedback.connect(sfxBus);
    }
    osc.start(t0);
    osc.stop(t0 + duration + 0.05);
  }

  const SYNTH = {
    // "Ding" de janela do sistema
    notify(ac) {
      tone(ac, { freq: 1320, duration: 0.09, gain: 0.12 });
      tone(ac, { freq: 1760, start: 0.08, duration: 0.16, gain: 0.1 });
    },
    // Abertura de painel importante: varredura curta e "holográfica"
    open(ac) {
      tone(ac, { freq: 520, duration: 0.22, type: "triangle", gain: 0.07, slideTo: 1560 });
      tone(ac, { freq: 2093, start: 0.16, duration: 0.12, gain: 0.05, echo: false });
    },
    // Quest concluída: arpejo maior curto
    quest(ac) {
      [784, 988, 1175, 1568].forEach((f, i) => tone(ac, { freq: f, start: i * 0.07, duration: 0.22, type: "triangle" }));
    },
    // Bônus: brilho rápido subindo
    bonus(ac) {
      [1175, 1480, 1760, 2349].forEach((f, i) => tone(ac, { freq: f, start: i * 0.045, duration: 0.14, gain: 0.1 }));
    },
    // Level up: subida longa + acorde sustentado
    levelup(ac) {
      [523, 659, 784, 1047, 1319, 1568].forEach((f, i) =>
        tone(ac, { freq: f, start: i * 0.08, duration: 0.25, type: "triangle", gain: 0.16 }));
      [1047, 1319, 1568].forEach((f) => tone(ac, { freq: f, start: 0.5, duration: 0.9, gain: 0.08 }));
    },
    // Punição / Penalty Zone: alarme grave descendente
    penalty(ac) {
      tone(ac, { freq: 220, duration: 0.35, type: "sawtooth", gain: 0.1, slideTo: 110, echo: false });
      tone(ac, { freq: 196, start: 0.4, duration: 0.5, type: "sawtooth", gain: 0.1, slideTo: 82, echo: false });
      tone(ac, { freq: 55, duration: 0.9, type: "sine", gain: 0.2, echo: false });
    },
    // Inicialização: zumbido grave subindo, como um sistema ligando
    boot(ac) {
      tone(ac, { freq: 60, duration: 1.4, type: "sine", gain: 0.16, slideTo: 140, echo: false });
      tone(ac, { freq: 240, start: 0.15, duration: 1.1, type: "triangle", gain: 0.05, slideTo: 480 });
      [0.35, 0.7, 1.05].forEach((t) => tone(ac, { freq: 1900, start: t, duration: 0.04, gain: 0.05, echo: false }));
    },
    // Sistema ativado: acorde aberto com brilho
    activate(ac) {
      [392, 587, 784].forEach((f) => tone(ac, { freq: f, duration: 0.9, type: "triangle", gain: 0.09 }));
      tone(ac, { freq: 1568, start: 0.12, duration: 0.5, gain: 0.07 });
    },
    // Conquista desbloqueada: sino em quinta + cintilar
    achievement(ac) {
      [880, 1319].forEach((f, i) => tone(ac, { freq: f, start: i * 0.12, duration: 0.6, gain: 0.12 }));
      [1760, 2093, 2637].forEach((f, i) => tone(ac, { freq: f, start: 0.3 + i * 0.06, duration: 0.18, gain: 0.06 }));
    },
    // Erro: dois bipes graves
    error(ac) {
      tone(ac, { freq: 180, duration: 0.12, type: "square", gain: 0.06, echo: false });
      tone(ac, { freq: 150, start: 0.15, duration: 0.16, type: "square", gain: 0.06, echo: false });
    },
  };

  let lastSynth = { name: "", at: 0 };

  function synth(name) {
    if (!SYNTH[name]) return;
    const now = Date.now();
    if (lastSynth.name === name && now - lastSynth.at < 250) return; // evita o mesmo som duas vezes seguidas
    lastSynth = { name, at: now };
    const ac = audio();
    if (!ac) return;
    try { SYNTH[name](ac); } catch (e) { /* som é opcional */ }
  }

  // ---------- Vozes (um canal só: uma nova interrompe a anterior) ----------
  const voices = {};
  let currentVoice = null;

  function voice(slot) {
    const url = mediaUrl(slot);
    if (!url) return null;
    let el = voices[slot];
    if (!el || el.dataset.src !== url) {
      el = new Audio();
      el.preload = "auto";
      el.src = url;
      el.dataset.src = url;
      voices[slot] = el;
    }
    return routed(el);
  }

  // Toca a voz; devolve uma Promise que resolve quando termina (ou falha).
  function playVoice(slot) {
    const el = voice(slot);
    if (!el) return Promise.reject(new Error("sem arquivo"));
    if (currentVoice && currentVoice !== el) { currentVoice.pause(); currentVoice.currentTime = 0; }
    currentVoice = el;
    setVolume(el, Math.min(1, prefs().sfxVolume * 1.1));
    el.currentTime = 0;
    duck(true);
    return el.play().then(() => new Promise((resolve) => {
      const done = () => { el.removeEventListener("ended", done); el.removeEventListener("pause", done); duck(false); resolve(); };
      el.addEventListener("ended", done);
      el.addEventListener("pause", done);
    })).catch((error) => { duck(false); throw error; });
  }

  function play(name) {
    const p = prefs();
    if (!p.sfx) return;
    if (VOICE_SLOTS.includes(name) && mediaUrl(name)) {
      playVoice(name).catch(() => synth(name));
      return;
    }
    synth(name);
  }

  // ---------- Música de fundo ----------
  let music = null;
  let musicWanted = false; // tentou tocar e foi bloqueado: tenta no próximo gesto
  let ducked = false;

  function musicEl() {
    const url = mediaUrl("music");
    if (!url) return null;
    if (!music || music.dataset.src !== url) {
      if (music) music.pause();
      music = new Audio();
      music.loop = true;
      music.preload = "none";
      music.src = url;
      music.dataset.src = url;
      music.addEventListener("timeupdate", rememberPosition);
    }
    return routed(music);
  }

  function musicVolume() {
    return prefs().musicVolume * (ducked ? 0.3 : 1);
  }

  function duck(on) {
    ducked = on;
    if (music) setVolume(music, musicVolume());
  }

  let lastSaved = 0;
  function rememberPosition() {
    if (!music || Date.now() - lastSaved < 2000) return;
    lastSaved = Date.now();
    try { storage("sessionStorage").setItem(MUSIC_POS_KEY, String(music.currentTime)); } catch (e) { /* ok */ }
  }

  function startMusic() {
    const p = prefs();
    if (!p.music || !inExperience()) return;
    const el = musicEl();
    if (!el || !el.paused) return;
    if (!el.dataset.resumed) {
      el.dataset.resumed = "1";
      try {
        const pos = parseFloat(storage("sessionStorage").getItem(MUSIC_POS_KEY) || "0");
        if (pos > 0) el.currentTime = pos;
      } catch (e) { /* ok */ }
    }
    setVolume(el, musicVolume());
    el.play().then(() => { musicWanted = false; }).catch(() => { musicWanted = true; });
  }

  function stopMusic() {
    musicWanted = false;
    if (music && !music.paused) music.pause();
  }

  // ---------- Áudio de entrada (uma vez por sessão do navegador) ----------
  let entrancePending = false;

  function entranceDone() {
    try { return storage("sessionStorage").getItem(ENTRANCE_KEY) === "1"; } catch (e) { return true; }
  }

  function markEntrance() {
    try { storage("sessionStorage").setItem(ENTRANCE_KEY, "1"); } catch (e) { /* ok */ }
  }

  // Chamado ao entrar na experiência principal (boot.js ou primeira página após o login).
  // Devolve true se a voz de entrada vai tocar (aí o boot não toca o zumbido sintetizado).
  function entrance() {
    const p = prefs();
    if (entrancePending) return true;
    if (!inExperience() || entranceDone()) return false;
    if (!p.entrance || !p.sfx || !mediaUrl("entrance")) { markEntrance(); return false; }
    markEntrance();
    entrancePending = true;
    playVoice("entrance")
      .then(() => { entrancePending = false; startMusic(); })
      .catch(() => { /* bloqueado: toca no primeiro gesto (ver unlock) */ });
    return true;
  }

  // ---------- Liberação pelo primeiro gesto ----------
  function unlock() {
    audio();
    if (entrancePending) {
      if (currentVoice && !currentVoice.paused) return; // já está tocando
      playVoice("entrance").then(() => { entrancePending = false; startMusic(); })
        .catch(() => { entrancePending = false; startMusic(); });
      return;
    }
    if (musicWanted || (prefs().music && music && music.paused)) startMusic();
  }
  ["pointerdown", "keydown", "touchend"].forEach((type) => document.addEventListener(type, unlock, { passive: true }));

  function applyPrefs(p) {
    if (sfxBus) sfxBus.gain.value = p.sfxVolume;
    if (music) setVolume(music, musicVolume());
    if (p.music) startMusic();
    else stopMusic();
  }

  // Cada página nova (Turbo ou recarregamento): começa a música se ela estiver ligada e não tocando.
  function onPage() {
    if (!inExperience()) { stopMusic(); return; }
    if (!entrance()) startMusic();
  }
  document.addEventListener("turbo:load", onPage);
  document.addEventListener("DOMContentLoaded", () => { if (!window.Turbo) onPage(); });
  window.addEventListener("pagehide", () => {
    if (music) { lastSaved = 0; rememberPosition(); }
  });

  // state(): leitura para depuração e testes de ponta a ponta.
  const state = () => ({
    musicPlaying: Boolean(music && !music.paused), musicTime: music ? music.currentTime : 0,
    musicVolume: music ? (music._gain ? music._gain.gain.value : music.volume) : null,
    entrancePending, entranceDone: entranceDone(), voice: currentVoice ? currentVoice.dataset.src : null,
  });
  window.ShadowAudio = { prefs, setPref, play, entrance, startMusic, stopMusic, state, hasMedia: (s) => Boolean(mediaUrl(s)) };
  // Compatibilidade com o código antigo (shadow.js, boot.js).
  window.ShadowSound = {
    play,
    enabled: () => prefs().sfx,
    setEnabled: (on) => setPref("sfx", on),
  };
})();
