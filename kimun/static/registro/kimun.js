/* Comportamiento de la interfaz de Kimün (diseno-interfaz.jpg). Sin dependencias.
   Todo es una mejora: sin JavaScript se puede escribir, adjuntar una foto, navegar y buscar en la lista. */
(function () {
  "use strict";

  const MAX_LADO_FOTO = 1600;      // px: bajo el límite de imagen de Bedrock y rápido de subir (PLAN.md, Task 8)
  const CALIDAD_FOTO = 0.85;
  const MAX_SEGUNDOS_AUDIO = 120;  // PLAN.md, Task 9

  function normalizar(texto) {
    return (texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
  }

  function minutos(segundos) {
    const s = Math.floor(segundos);
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  }

  function ponerArchivo(input, archivo) {
    // Reemplaza el archivo de un <input type="file">. Si el navegador no lo permite, deja el original.
    try {
      const datos = new DataTransfer();
      if (archivo) datos.items.add(archivo);
      input.files = datos.files;
      return true;
    } catch (error) {
      return false;
    }
  }

  /* --- Menú lateral (pantalla III) --- */

  function iniciarMenu() {
    const menu = document.getElementById("menu-lateral");
    if (!menu || typeof menu.showModal !== "function") return;
    const botones = document.querySelectorAll("[data-abrir-menu]");
    let origen = null;

    botones.forEach(function (boton) {
      boton.addEventListener("click", function () {
        origen = boton;
        menu.showModal();
        boton.setAttribute("aria-expanded", "true");
        const buscador = menu.querySelector("[data-buscador]");
        if (buscador && window.matchMedia("(pointer: fine)").matches) buscador.focus();
      });
    });
    menu.addEventListener("close", function () {
      botones.forEach(function (b) { b.setAttribute("aria-expanded", "false"); });
      if (origen) origen.focus();
    });
    // Un toque fuera del panel (sobre el fondo del <dialog>) lo cierra.
    menu.addEventListener("click", function (evento) {
      if (evento.target === menu) menu.close();
    });
    menu.querySelectorAll("[data-cerrar-menu]").forEach(function (b) {
      b.addEventListener("click", function () { menu.close(); });
    });
  }

  function iniciarBuscador() {
    const buscador = document.querySelector("[data-buscador]");
    const lista = document.querySelector("[data-lista-ninos]");
    if (!buscador || !lista) return;
    const resultado = document.querySelector("[data-resultado-busqueda]");
    const vacio = document.querySelector("[data-sin-resultados]");
    const items = Array.from(lista.querySelectorAll("li[data-nombre]"));

    buscador.addEventListener("input", function () {
      const buscado = normalizar(buscador.value);
      let visibles = 0;
      items.forEach(function (item) {
        const coincide = !buscado || normalizar(item.dataset.nombre).includes(buscado);
        item.hidden = !coincide;
        if (coincide) visibles += 1;
      });
      if (vacio) vacio.hidden = visibles > 0;
      if (resultado) {
        resultado.textContent = buscado ? visibles + (visibles === 1 ? " resultado" : " resultados") : "";
      }
    });
  }

  /* --- Perfil: abrir el detalle de un núcleo desde el resumen o desde #nucleo-XX --- */

  function abrirDetalle(sigla) {
    const detalle = document.querySelector('[data-detalle="' + CSS.escape(sigla) + '"]');
    if (detalle) detalle.open = true;
  }

  function iniciarDetalles() {
    document.querySelectorAll("[data-abrir-detalle]").forEach(function (enlace) {
      enlace.addEventListener("click", function () { abrirDetalle(enlace.dataset.abrirDetalle); });
    });
    const desdeHash = function () {
      const coincide = /^#nucleo-(.+)$/.exec(window.location.hash);
      if (!coincide) return;
      abrirDetalle(decodeURIComponent(coincide[1]));
      const destino = document.getElementById("nucleo-" + decodeURIComponent(coincide[1]));
      if (destino) destino.scrollIntoView();
    };
    window.addEventListener("hashchange", desdeHash);
    desdeHash();
  }

  /* --- Registrar (pantalla I): texto, foto y audio --- */

  function achicarFoto(archivo) {
    return new Promise(function (resolver) {
      if (!archivo || !archivo.type.startsWith("image/")) return resolver(archivo);
      const url = URL.createObjectURL(archivo);
      const imagen = new Image();
      imagen.onload = function () {
        const escala = Math.min(1, MAX_LADO_FOTO / Math.max(imagen.naturalWidth, imagen.naturalHeight));
        if (escala === 1 && archivo.type === "image/jpeg") {
          URL.revokeObjectURL(url);
          return resolver(archivo);
        }
        const lienzo = document.createElement("canvas");
        lienzo.width = Math.round(imagen.naturalWidth * escala);
        lienzo.height = Math.round(imagen.naturalHeight * escala);
        lienzo.getContext("2d").drawImage(imagen, 0, 0, lienzo.width, lienzo.height);
        URL.revokeObjectURL(url);
        lienzo.toBlob(function (blob) {
          resolver(blob ? new File([blob], "foto.jpg", { type: "image/jpeg" }) : archivo);
        }, "image/jpeg", CALIDAD_FOTO);
      };
      imagen.onerror = function () {
        URL.revokeObjectURL(url);
        resolver(archivo);  // por ejemplo HEIC en un navegador que no lo dibuja: se sube tal cual
      };
      imagen.src = url;
    });
  }

  function iniciarComposer(form) {
    const texto = form.querySelector("[data-texto]");
    const foto = form.querySelector("[data-foto]");
    const audio = form.querySelector("[data-audio]");
    const microfono = form.querySelector("[data-microfono]");
    const microfonoTexto = form.querySelector("[data-microfono-texto]");
    const estado = form.querySelector("[data-estado]");
    const adjunto = form.querySelector("[data-adjunto]");
    const vistaPrevia = form.querySelector("[data-vista-previa]");
    const escuchar = form.querySelector("[data-escuchar]");
    const adjuntoTexto = form.querySelector("[data-adjunto-texto]");
    const quitar = form.querySelector("[data-quitar-adjunto]");
    let urlAdjunto = null;

    function decir(mensaje) { if (estado) estado.textContent = mensaje || ""; }

    function crecer() {
      texto.style.height = "auto";
      texto.style.height = Math.min(texto.scrollHeight, 160) + "px";
    }
    if (texto) {
      texto.addEventListener("input", crecer);
      crecer();
      // Enter envía en computadores; Mayús + Enter hace un salto de línea. En el teléfono, Enter es salto de línea.
      texto.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" && !evento.shiftKey && window.matchMedia("(pointer: fine)").matches) {
          evento.preventDefault();
          if (form.requestSubmit) form.requestSubmit(); else form.submit();
        }
      });
    }

    function mostrarAdjunto(tipo, archivo, descripcion) {
      if (urlAdjunto) URL.revokeObjectURL(urlAdjunto);
      urlAdjunto = archivo ? URL.createObjectURL(archivo) : null;
      vistaPrevia.hidden = tipo !== "foto";
      escuchar.hidden = tipo !== "audio";
      if (tipo === "foto") vistaPrevia.src = urlAdjunto;
      if (tipo === "audio") escuchar.src = urlAdjunto;
      adjuntoTexto.textContent = descripcion || "";
      adjunto.hidden = !archivo;
    }

    function quitarAdjunto() {
      ponerArchivo(foto, null);
      if (audio) ponerArchivo(audio, null);
      foto.value = "";
      mostrarAdjunto(null, null, "");
      decir("");
    }
    if (quitar) quitar.addEventListener("click", quitarAdjunto);

    if (foto) {
      foto.addEventListener("change", function () {
        const original = foto.files && foto.files[0];
        if (!original) return quitarAdjunto();
        if (audio) ponerArchivo(audio, null);
        decir("Preparando la foto…");
        achicarFoto(original).then(function (achicada) {
          ponerArchivo(foto, achicada);
          mostrarAdjunto("foto", achicada, "Foto lista para enviar. Puedes agregar una nota.");
          decir("");
        });
      });
    }

    // Audio: solo si el navegador puede grabar (requiere HTTPS o localhost).
    const puedeGrabar = microfono && audio && window.MediaRecorder && navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === "function";
    if (!puedeGrabar) {
      // Con http://<ip>:8000 desde el teléfono el navegador no da el micrófono: se avisa en vez de esconderlo sin más.
      if (microfono && !window.isSecureContext) {
        decir("Para grabar audio, abre Kimün con https:// (la dirección de CloudFront).");
      }
      return;
    }
    microfono.hidden = false;
    let grabador = null;
    let partes = [];
    let inicio = 0;
    let reloj = null;
    let corte = null;

    function tipoDeAudio() {
      const tipos = ["audio/webm;codecs=opus", "audio/mp4", "audio/ogg;codecs=opus", "audio/webm"];
      return tipos.find(function (t) { return MediaRecorder.isTypeSupported(t); }) || "";
    }

    function terminar() {
      if (grabador && grabador.state !== "inactive") grabador.stop();
    }

    microfono.addEventListener("click", function () {
      if (grabador && grabador.state === "recording") return terminar();
      navigator.mediaDevices.getUserMedia({ audio: true }).then(function (flujo) {
        const tipo = tipoDeAudio();
        grabador = tipo ? new MediaRecorder(flujo, { mimeType: tipo }) : new MediaRecorder(flujo);
        partes = [];
        grabador.addEventListener("dataavailable", function (e) { if (e.data && e.data.size) partes.push(e.data); });
        grabador.addEventListener("stop", function () {
          clearInterval(reloj);
          clearTimeout(corte);
          flujo.getTracks().forEach(function (pista) { pista.stop(); });
          microfono.setAttribute("aria-pressed", "false");
          microfonoTexto.textContent = "Grabar un audio";
          const segundos = (Date.now() - inicio) / 1000;
          const mime = (grabador.mimeType || "audio/webm").split(";")[0];
          const extension = mime.includes("mp4") ? "m4a" : mime.includes("ogg") ? "ogg" : "webm";
          const archivo = new File(partes, "audio." + extension, { type: mime });
          ponerArchivo(foto, null);
          foto.value = "";
          if (ponerArchivo(audio, archivo)) {
            mostrarAdjunto("audio", archivo, "Audio de " + minutos(segundos) + " listo para enviar.");
            decir("");
          } else {
            decir("Este navegador no permite adjuntar la grabación. Escribe la nota, por favor.");
          }
        });
        grabador.start();
        inicio = Date.now();
        microfono.setAttribute("aria-pressed", "true");
        microfonoTexto.textContent = "Detener la grabación";
        decir("Grabando… 0:00 (toca de nuevo el micrófono para terminar)");
        reloj = setInterval(function () {
          decir("Grabando… " + minutos((Date.now() - inicio) / 1000) + " (toca de nuevo el micrófono para terminar)");
        }, 1000);
        corte = setTimeout(terminar, MAX_SEGUNDOS_AUDIO * 1000);
      }).catch(function () {
        decir("No se pudo usar el micrófono. Revisa el permiso del navegador o escribe la nota.");
      });
    });
  }

  function iniciar() {
    iniciarMenu();
    iniciarBuscador();
    iniciarDetalles();
    document.querySelectorAll("[data-composer]").forEach(iniciarComposer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
