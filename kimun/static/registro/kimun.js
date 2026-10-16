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

    // Arrastrar una foto a la barra. El <input type="file"> está oculto y no recibe el arrastre: sin esto el
    // navegador abre la imagen en la pestaña y se pierde lo escrito. Se reusa el mismo camino que "+".
    if (foto) {
      const barra = form.querySelector(".composer-barra") || form;
      const traeArchivos = function (evento) {
        return evento.dataTransfer && Array.from(evento.dataTransfer.types || []).includes("Files");
      };
      let profundidad = 0;
      form.addEventListener("dragenter", function (evento) {
        if (!traeArchivos(evento)) return;
        evento.preventDefault();
        profundidad += 1;
        barra.classList.add("composer-soltar");
      });
      form.addEventListener("dragover", function (evento) {
        if (!traeArchivos(evento)) return;
        evento.preventDefault();
        evento.dataTransfer.dropEffect = "copy";
      });
      form.addEventListener("dragleave", function () {
        profundidad = Math.max(0, profundidad - 1);
        if (!profundidad) barra.classList.remove("composer-soltar");
      });
      form.addEventListener("drop", function (evento) {
        if (!traeArchivos(evento)) return;
        evento.preventDefault();
        profundidad = 0;
        barra.classList.remove("composer-soltar");
        const imagen = Array.from(evento.dataTransfer.files).find(function (a) { return a.type.startsWith("image/"); });
        if (!imagen) return decir("Solo se puede soltar una foto. Para un audio, usa el micrófono.");
        if (!ponerArchivo(foto, imagen)) return decir("Este navegador no permite soltar la foto. Usa el botón «+».");
        foto.dispatchEvent(new Event("change", { bubbles: true }));
      });
      // Si la foto cae fuera de la barra, no se abre en la pestaña (se perdería la nota escrita).
      ["dragover", "drop"].forEach(function (tipo) {
        document.addEventListener(tipo, function (evento) {
          if (traeArchivos(evento) && !form.contains(evento.target)) evento.preventDefault();
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

  /* --- Gráfico de flor de la ficha (registro/radar.py) ---
     El SVG llega armado del servidor; aquí solo se le suma lo que ayuda a leerlo de un vistazo:
     el color de cada núcleo (el mismo de los escalones de la tabla), los números de la escala en los
     anillos y, en pantallas angostas, una versión compacta: sin los nombres (están en la tabla de al
     lado) y con el ícono de cada núcleo en la punta de su pétalo. Sin JS se ve el SVG original. */

  const SVG_NS = "http://www.w3.org/2000/svg";
  const ANCHO_COMPACTO = 480;
  // Nombres para el modo compacto. Los de los lados (CM, CES) son los más cortos: ahí hay menos espacio.
  const NOMBRES_CORTOS = {
    IA: "Id. y Autonomía", CC: "Conv. y Ciudad.", CM: "Corp. y Mov.", LV: "L. Verbal",
    LA: "L. Artísticos", EEN: "Entorno Natural", CES: "Entorno Soc.", PM: "Pens. Matemático",
  };

  function iniciarFlor(figura) {
    const svg = figura.querySelector("svg.radar");
    if (!svg) return;
    const anillos = svg.querySelectorAll(".radar-anillo");
    const petalos = Array.from(svg.querySelectorAll(".radar-petalo"));
    if (!anillos.length || !petalos.length) return;
    const siglas = (figura.dataset.siglas || "").split(" ");
    const total = petalos.length;
    const cx = parseFloat(anillos[0].getAttribute("cx"));
    const cy = parseFloat(anillos[0].getAttribute("cy"));
    const radioMax = parseFloat(anillos[anillos.length - 1].getAttribute("r"));
    const angulo = function (i) { return -Math.PI / 2 + 2 * Math.PI * i / total; };
    const indiceDe = function (x, y) {
      const a = Math.atan2(y - cy, x - cx) + Math.PI / 2;
      return ((Math.round(a / (2 * Math.PI / total)) % total) + total) % total;
    };
    const pintar = function (el, i) { if (siglas[i]) el.classList.add("nucleo-" + siglas[i]); };

    // Un anillo por nivel, del 1 al máximo: los escalones de la tabla usan el mismo máximo.
    const seccion = figura.closest("[data-niveles]");
    if (seccion) seccion.style.setProperty("--nivel-max", anillos.length);
    anillos[anillos.length - 1].classList.add("radar-anillo-max");

    petalos.forEach(function (p, i) { pintar(p, i); p.dataset.sigla = siglas[i] || ""; });

    // Nivel de cada pétalo, leído de su <title> ("Lenguaje Verbal: 2" o "…: 5 · Integrando").
    const datos = petalos.map(function (p) {
      const titulo = (p.querySelector("title") || {}).textContent || "";
      const nivel = titulo.match(/:\s*(\d+)/);
      return { nombre: titulo.split(":")[0], nivel: nivel ? parseInt(nivel[1], 10) : null };
    });
    // El núcleo más bajo respecto del esperado (si hay empate, todos). Si ninguno está bajo, ninguno.
    const esperado = parseInt(figura.dataset.esperado, 10);
    if (!isNaN(esperado)) {
      const diferencias = datos.map(function (d) { return d.nivel === null ? Infinity : d.nivel - esperado; });
      const peor = Math.min.apply(null, diferencias);
      if (peor < 0) datos.forEach(function (d, i) { d.masBajo = diferencias[i] === peor; });
    }
    petalos.forEach(function (p, i) { if (datos[i].masBajo) p.classList.add("flor-mas-bajo"); });
    svg.querySelectorAll(".radar-punto").forEach(function (c) {
      pintar(c, indiceDe(parseFloat(c.getAttribute("cx")), parseFloat(c.getAttribute("cy"))));
    });

    // Íconos: el número de la máscara (radar-icono-N) es el del pétalo.
    const iconos = [];
    svg.querySelectorAll("rect.radar-icono").forEach(function (rect) {
      const id = (rect.getAttribute("mask") || "").match(/#([^)]+)/);
      const mascara = id ? svg.querySelector("#" + id[1]) : null;
      const i = id ? parseInt(id[1].split("-").pop(), 10) : 0;
      pintar(rect, i);
      const lado = parseFloat(rect.getAttribute("width"));
      const r = radioMax + lado * 0.7;
      iconos.push({
        piezas: [rect, mascara, mascara && mascara.querySelector("image")],
        original: [rect.getAttribute("x"), rect.getAttribute("y")],
        compacta: [(cx + r * Math.cos(angulo(i)) - lado / 2).toFixed(1), (cy + r * Math.sin(angulo(i)) - lado / 2).toFixed(1)],
      });
    });

    // Escala: el número de cada nivel sobre su anillo, entre el primer y el segundo pétalo.
    const escala = document.createElementNS(SVG_NS, "g");
    escala.setAttribute("class", "radar-escala");
    escala.setAttribute("aria-hidden", "true");
    const entre = angulo(0) + Math.PI / total;
    anillos.forEach(function (anillo, i) {
      const nivel = i + 1;
      if (nivel % 2 === 0) return;  // solo los impares: todos juntos se montan
      const r = parseFloat(anillo.getAttribute("r"));
      const texto = document.createElementNS(SVG_NS, "text");
      texto.setAttribute("x", (cx + r * Math.cos(entre)).toFixed(1));
      texto.setAttribute("y", (cy + r * Math.sin(entre) + 4).toFixed(1));
      texto.setAttribute("text-anchor", "middle");
      texto.textContent = nivel;
      escala.appendChild(texto);
    });
    svg.appendChild(escala);

    // Etiquetas del modo compacto: junto al ícono de la punta, el nombre corto (tinta) y «nivel N» (color
    // oscuro del núcleo). Ancladas como en radar.py: start a la derecha, end a la izquierda, middle arriba y abajo.
    const LADO = 20, ALTO_LINEA = 18;
    const etiquetas = document.createElementNS(SVG_NS, "g");
    etiquetas.setAttribute("class", "flor-etiquetas");
    etiquetas.setAttribute("aria-hidden", "true");  // el SVG ya tiene su descripción (aria-label) y la tabla
    datos.forEach(function (d, i) {
      const a = angulo(i), coseno = Math.cos(a), seno = Math.sin(a);
      const r = radioMax + LADO * 0.7;
      const ix = cx + r * coseno, iy = cy + r * seno;
      let x = ix, y, anclaje = "middle";
      if (coseno > 0.3) { anclaje = "start"; x = ix + LADO / 2 + 4; y = iy - 2; }
      else if (coseno < -0.3) { anclaje = "end"; x = ix - LADO / 2 - 4; y = iy - 2; }
      else if (seno < 0) { y = iy - LADO / 2 - 6 - ALTO_LINEA; }
      else { y = iy + LADO / 2 + 18; }
      const texto = document.createElementNS(SVG_NS, "text");
      texto.setAttribute("class", "flor-etiqueta" + (d.masBajo ? " flor-mas-bajo" : ""));
      pintar(texto, i);
      texto.setAttribute("x", x.toFixed(1));
      texto.setAttribute("y", y.toFixed(1));
      texto.setAttribute("text-anchor", anclaje);
      const nombre = document.createElementNS(SVG_NS, "tspan");
      nombre.setAttribute("x", x.toFixed(1));
      if (d.masBajo) {
        const alerta = document.createElementNS(SVG_NS, "tspan");
        alerta.setAttribute("class", "flor-alerta");
        alerta.textContent = "\u26A0\uFE0E ";  // ⚠ como texto, no emoji: así toma el color de alerta
        nombre.appendChild(alerta);
      }
      nombre.appendChild(document.createTextNode(NOMBRES_CORTOS[siglas[i]] || d.nombre));
      const nivel = document.createElementNS(SVG_NS, "tspan");
      nivel.setAttribute("class", "flor-nivel");
      nivel.setAttribute("x", x.toFixed(1));
      nivel.setAttribute("dy", ALTO_LINEA);
      nivel.textContent = d.nivel === null ? "sin nivel" : "nivel " + d.nivel;
      texto.appendChild(nombre);
      texto.appendChild(nivel);
      etiquetas.appendChild(texto);
    });
    svg.appendChild(etiquetas);

    // Modo compacto: se recorta el dibujo a la flor y sus etiquetas, y los íconos pasan a la punta de los
    // pétalos. Más margen a los lados que arriba y abajo: ahí las etiquetas crecen a lo ancho.
    const vistaOriginal = svg.getAttribute("viewBox");
    const margenLado = 140, margenAlto = 78;
    const vistaCompacta = [cx - radioMax - margenLado, cy - radioMax - margenAlto, 2 * (radioMax + margenLado), 2 * (radioMax + margenAlto)].join(" ");
    let compacta = null;
    // Se mide el espacio de la figura (ancho + márgenes), no la figura sola: en modo compacto su margen
    // negativo (registro.css) la ensancha ~35 px; medida sola, salía y volvía a entrar al modo compacto en
    // cada cuadro y la pantalla temblaba. Ancho + márgenes es el mismo en los dos modos.
    const anchoDisponible = function () {
      const estilo = getComputedStyle(figura);
      return figura.getBoundingClientRect().width + parseFloat(estilo.marginLeft) + parseFloat(estilo.marginRight);
    };
    const ajustar = function () {
      const ahora = anchoDisponible() < ANCHO_COMPACTO;
      if (ahora === compacta) return;
      compacta = ahora;
      figura.classList.toggle("flor-compacta", compacta);
      svg.setAttribute("viewBox", compacta ? vistaCompacta : vistaOriginal);
      iconos.forEach(function (icono) {
        const xy = compacta ? icono.compacta : icono.original;
        icono.piezas.forEach(function (el) { if (el) { el.setAttribute("x", xy[0]); el.setAttribute("y", xy[1]); } });
      });
    };
    ajustar();
    // Se observa el contenedor: su ancho no cambia al entrar o salir del modo compacto.
    if ("ResizeObserver" in window) new ResizeObserver(ajustar).observe(figura.parentElement || figura);

    // Al pasar por una fila de la tabla, se destaca su pétalo.
    const seccionTabla = seccion || document;
    seccionTabla.querySelectorAll("tr[data-sigla]").forEach(function (fila) {
      const petalo = petalos.find(function (p) { return p.dataset.sigla === fila.dataset.sigla; });
      if (!petalo) return;
      const marcar = function (si) { svg.classList.toggle("con-resaltado", si); petalo.classList.toggle("resaltado", si); };
      fila.addEventListener("mouseenter", function () { marcar(true); });
      fila.addEventListener("mouseleave", function () { marcar(false); });
      fila.addEventListener("focusin", function () { marcar(true); });
      fila.addEventListener("focusout", function () { marcar(false); });
    });
  }

  /* --- Informe para la familia: imprimir o guardar en PDF --- */

  function iniciarImprimir() {
    document.querySelectorAll("[data-imprimir]").forEach(function (boton) {
      boton.addEventListener("click", function () { window.print(); });
    });
  }

  function iniciar() {
    iniciarImprimir();
    iniciarMenu();
    iniciarBuscador();
    iniciarDetalles();
    document.querySelectorAll("[data-composer]").forEach(iniciarComposer);
    document.querySelectorAll("[data-flor]").forEach(iniciarFlor);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
