// Efeitos sonoros do System, sintetizados na hora com a Web Audio API.
// São sons originais (nenhum arquivo de áudio, nada copiado do anime): tons curtos, brilhantes e
// "holográficos" para ganhos, e graves para alertas e punições.
//
// Uso: ShadowSound.play("quest" | "levelup" | "penalty" | "error" | "notify" | "bonus")
// Liga/desliga fica salvo no navegador (localStorage "shadow.sound").
(function () {
  const STORAGE_KEY = "shadow.sound";
  let ctx = null;

  function enabled() {
    try { return localStorage.getItem(STORAGE_KEY) !== "off"; } catch (e) { return true; }
  }

  function setEnabled(on) {
    try { localStorage.setItem(STORAGE_KEY, on ? "on" : "off"); } catch (e) { /* sem armazenamento */ }
  }

  function audio() {
    if (!ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      ctx = new AudioCtx();
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
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
    amp.connect(ac.destination);
    if (echo) {
      const delay = ac.createDelay();
      const feedback = ac.createGain();
      delay.delayTime.value = 0.11;
      feedback.gain.value = 0.28;
      amp.connect(delay);
      delay.connect(feedback);
      feedback.connect(ac.destination);
    }
    osc.start(t0);
    osc.stop(t0 + duration + 0.05);
  }

  const SOUNDS = {
    // "Ding" de janela do sistema
    notify(ac) {
      tone(ac, { freq: 1320, duration: 0.09, gain: 0.12 });
      tone(ac, { freq: 1760, start: 0.08, duration: 0.16, gain: 0.1 });
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
    // Erro: dois bipes graves
    error(ac) {
      tone(ac, { freq: 180, duration: 0.12, type: "square", gain: 0.06, echo: false });
      tone(ac, { freq: 150, start: 0.15, duration: 0.16, type: "square", gain: 0.06, echo: false });
    },
  };

  function play(name) {
    if (!enabled() || !SOUNDS[name]) return;
    const ac = audio();
    if (!ac) return;
    try { SOUNDS[name](ac); } catch (e) { /* som é opcional */ }
  }

  window.ShadowSound = { play, enabled, setEnabled };
})();
