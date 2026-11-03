// Sequência de inicialização do System. Curta (~3 s), pula com clique, Esc ou qualquer tecla.
// Com mídia cadastrada, mostra a arte da inicialização e toca a voz de entrada (ver sounds.js).
// Modo vem do servidor (Dashboard > Personalizar): "session" = uma vez por sessão do navegador,
// "dashboard" = toda vez que o Dashboard abre, "off" = o elemento nem é enviado.
(function () {
  const SESSION_KEY = "shadow.booted";

  function shouldRun(el) {
    const mode = el.dataset.bootMode;
    if (mode === "dashboard") return el.dataset.bootPage === "dashboard.index";
    try {
      return !window.sessionStorage.getItem(SESSION_KEY);
    } catch (e) {
      return false; // sem sessionStorage (modo privado restrito): não insiste em mostrar
    }
  }

  function markDone() {
    try { window.sessionStorage.setItem(SESSION_KEY, "1"); } catch (e) { /* sem storage: ok */ }
  }

  function run() {
    const el = document.querySelector("[data-boot]");
    if (!el || el.dataset.booting || !shouldRun(el)) return;
    el.dataset.booting = "1";

    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const lines = Array.from(el.querySelectorAll(".boot-log li"));
    const timers = [];
    let finished = false;

    const finish = () => {
      if (finished) return;
      finished = true;
      timers.forEach(clearTimeout);
      markDone();
      el.classList.add("is-leaving");
      setTimeout(() => { el.hidden = true; el.remove(); }, reduced ? 0 : 450);
      document.removeEventListener("keydown", onKey);
    };
    const onKey = () => finish();

    el.hidden = false;
    document.addEventListener("keydown", onKey);
    el.addEventListener("click", finish);

    const sound = (name) => { if (window.ShadowSound) window.ShadowSound.play(name); };
    // Voz de entrada ("Se esse sistema tá querendo me usar..."): uma vez por sessão. Com ela tocando, o
    // zumbido sintetizado do boot não toca por cima.
    const voiced = Boolean(window.ShadowAudio && window.ShadowAudio.entrance());

    if (reduced) {
      // Sem animação: mostra tudo de uma vez e sai rápido.
      lines.forEach((li) => li.classList.add("is-on"));
      el.classList.add("show-manifesto", "is-static");
      timers.push(setTimeout(finish, 1600));
      return;
    }

    if (!voiced) sound("boot");
    const step = 330;
    lines.forEach((li, i) => {
      timers.push(setTimeout(() => {
        li.classList.add("is-on");
        el.style.setProperty("--boot-progress", `${Math.round(((i + 1) / lines.length) * 100)}%`);
        if (i === lines.length - 1 && !voiced) sound("activate");
      }, 200 + i * step));
    });
    const manifestoAt = 200 + lines.length * step + 150;
    timers.push(setTimeout(() => el.classList.add("show-manifesto"), manifestoAt));
    timers.push(setTimeout(finish, manifestoAt + 1700));
  }

  // Turbo dispara turbo:load na primeira carga e a cada navegação; sem Turbo, vale o DOMContentLoaded.
  document.addEventListener("turbo:load", run);
  document.addEventListener("DOMContentLoaded", () => { if (!window.Turbo) run(); });
})();
