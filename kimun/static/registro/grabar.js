// Grabación de audio en la pantalla de captura (PLAN.md, Task 9).
// Sin MediaRecorder o sin DataTransfer no hace nada: queda el campo de archivo del formulario.
// La grabación se pone en ese mismo campo, así que se envía con el botón «Guardar audio».
(() => {
  "use strict";
  const form = document.getElementById("form-audio");
  const campo = form && form.querySelector('input[type="file"]');
  const soportado =
    window.MediaRecorder && navigator.mediaDevices && navigator.mediaDevices.getUserMedia &&
    typeof DataTransfer === "function";
  if (!campo || !soportado) return;

  const MAX_SEGUNDOS = 120;
  // Android y escritorio graban WebM/Opus; Safari en iPhone, MP4. Transcribe acepta ambos.
  const TIPOS = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm", "audio/ogg;codecs=opus"];
  const tipoPreferido = TIPOS.find((t) => MediaRecorder.isTypeSupported(t)) || "";

  const grabadora = document.getElementById("grabadora");
  const botonGrabar = document.getElementById("grabar");
  const botonDetener = document.getElementById("detener");
  const estado = document.getElementById("estado-grabacion");
  const tiempo = document.getElementById("tiempo-grabacion");
  const vistaPrevia = document.getElementById("vista-previa");

  grabadora.hidden = false;
  // Con la grabadora de la página, el campo queda para elegir un audio ya grabado.
  campo.removeAttribute("capture");

  let grabador = null;
  let trozos = [];
  let inicio = 0;
  let reloj = null;
  let urlVistaPrevia = null;
  let porLimite = false;

  const mmss = (segundos) => {
    const s = Math.floor(segundos);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };

  const alDetener = (flujo) => {
    clearInterval(reloj);
    flujo.getTracks().forEach((pista) => pista.stop());
    const tipo = grabador.mimeType || tipoPreferido || "audio/webm";
    const extension = tipo.includes("mp4") ? "mp4" : tipo.includes("ogg") ? "ogg" : "webm";
    const audio = new Blob(trozos, { type: tipo });
    const transferencia = new DataTransfer();
    transferencia.items.add(new File([audio], `grabacion.${extension}`, { type: tipo }));
    campo.files = transferencia.files;

    if (urlVistaPrevia) URL.revokeObjectURL(urlVistaPrevia);
    urlVistaPrevia = URL.createObjectURL(audio);
    vistaPrevia.src = urlVistaPrevia;
    vistaPrevia.hidden = false;

    const duracion = mmss((Date.now() - inicio) / 1000);
    tiempo.textContent = "";
    estado.textContent =
      (porLimite ? "Se detuvo al llegar a 2 minutos. " : "") +
      `Grabación lista (${duracion}). Escúchala y presiona «Guardar audio», o graba de nuevo.`;
    botonGrabar.textContent = "Grabar de nuevo";
    botonGrabar.disabled = false;
    botonDetener.disabled = true;
    botonGrabar.focus();
  };

  botonGrabar.addEventListener("click", async () => {
    let flujo;
    try {
      flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      estado.textContent =
        "No se pudo usar el micrófono. Revisa el permiso del navegador o elige un audio grabado con otra app.";
      return;
    }
    trozos = [];
    porLimite = false;
    grabador = new MediaRecorder(flujo, tipoPreferido ? { mimeType: tipoPreferido } : undefined);
    grabador.addEventListener("dataavailable", (evento) => {
      if (evento.data && evento.data.size) trozos.push(evento.data);
    });
    grabador.addEventListener("stop", () => alDetener(flujo));
    grabador.start(1000);
    inicio = Date.now();

    botonGrabar.disabled = true;
    botonDetener.disabled = false;
    botonDetener.focus();
    estado.textContent = "Grabando. Presiona «Detener» al terminar.";
    tiempo.textContent = "0:00 de 2:00";
    reloj = setInterval(() => {
      const segundos = (Date.now() - inicio) / 1000;
      if (segundos >= MAX_SEGUNDOS) {
        porLimite = true;
        grabador.stop();
        return;
      }
      tiempo.textContent = `${mmss(segundos)} de 2:00`;
    }, 500);
  });

  botonDetener.addEventListener("click", () => {
    if (grabador && grabador.state === "recording") grabador.stop();
  });

  // Si se envía mientras graba, primero se detiene para no mandar un archivo vacío.
  form.addEventListener("submit", (evento) => {
    if (grabador && grabador.state === "recording") {
      evento.preventDefault();
      grabador.addEventListener("stop", () => form.requestSubmit(), { once: true });
      grabador.stop();
    }
  });
})();
