/*
 * Captura por foto (Task 8). Achica la foto en el teléfono antes de subirla:
 * lado mayor de 1600 px, en JPEG. Así queda bajo el límite de imagen de Bedrock
 * (3,75 MB) y sube rápido con poca señal. Al volver a dibujarla en un canvas
 * también se pierden los metadatos EXIF (por ejemplo, la ubicación GPS).
 *
 * Si algo falla (navegador antiguo), se sube la foto tal cual y el servidor
 * la rechaza con un mensaje si pasa del máximo.
 */
(function () {
  "use strict";

  var LADO_MAXIMO = 1600;
  var CALIDAD = 0.85;

  var form = document.querySelector("[data-captura-foto]");
  if (!form) return;
  var input = form.querySelector('input[type="file"]');
  var estado = form.querySelector("[data-estado]");
  var vista = form.querySelector("[data-vista-previa]");
  var boton = form.querySelector("[data-enviar]");
  var urlVista = null;

  function cargarConImg(archivo) {
    return new Promise(function (resolver, rechazar) {
      var url = URL.createObjectURL(archivo);
      var img = new Image();
      img.onload = function () { URL.revokeObjectURL(url); resolver(img); };
      img.onerror = function () { URL.revokeObjectURL(url); rechazar(new Error("No se pudo leer la imagen")); };
      img.src = url;
    });
  }

  function cargar(archivo) {
    // createImageBitmap respeta la orientación EXIF; si no existe o falla, se usa <img>.
    if (window.createImageBitmap) {
      return createImageBitmap(archivo, { imageOrientation: "from-image" }).catch(function () {
        return cargarConImg(archivo);
      });
    }
    return cargarConImg(archivo);
  }

  function achicar(archivo) {
    return cargar(archivo).then(function (imagen) {
      var escala = Math.min(1, LADO_MAXIMO / Math.max(imagen.width, imagen.height));
      var canvas = document.createElement("canvas");
      canvas.width = Math.round(imagen.width * escala);
      canvas.height = Math.round(imagen.height * escala);
      var ctx = canvas.getContext("2d");
      ctx.fillStyle = "#fff"; // fondo blanco para PNG con transparencia
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(imagen, 0, 0, canvas.width, canvas.height);
      if (imagen.close) imagen.close();
      return new Promise(function (resolver, rechazar) {
        canvas.toBlob(function (blob) {
          if (blob) resolver({ blob: blob, ancho: canvas.width, alto: canvas.height });
          else rechazar(new Error("No se pudo convertir la imagen"));
        }, "image/jpeg", CALIDAD);
      });
    });
  }

  function mostrarVista(blob) {
    if (urlVista) URL.revokeObjectURL(urlVista);
    urlVista = URL.createObjectURL(blob);
    vista.src = urlVista;
    vista.hidden = false;
  }

  input.addEventListener("change", function () {
    var archivo = input.files && input.files[0];
    if (!archivo) {
      vista.hidden = true;
      estado.textContent = "";
      return;
    }
    if (archivo.type && archivo.type.indexOf("image/") !== 0) {
      // Un PDF (hoja de un instrumento, Task 14) se sube tal cual.
      vista.hidden = true;
      estado.textContent = "Archivo listo para subir (" + Math.max(1, Math.round(archivo.size / 1024)) + " KB).";
      return;
    }
    boton.disabled = true;
    estado.textContent = "Preparando la foto…";
    achicar(archivo)
      .then(function (r) {
        var dt = new DataTransfer();
        dt.items.add(new File([r.blob], "foto.jpg", { type: "image/jpeg", lastModified: Date.now() }));
        input.files = dt.files;
        mostrarVista(r.blob);
        estado.textContent = "Foto lista para subir (" + r.ancho + " × " + r.alto + " px, " +
          Math.max(1, Math.round(r.blob.size / 1024)) + " KB).";
      })
      .catch(function () {
        mostrarVista(archivo);
        estado.textContent = "No se pudo achicar la foto en este teléfono; se subirá tal cual.";
      })
      .then(function () { boton.disabled = false; });
  });

  form.addEventListener("submit", function () {
    boton.setAttribute("aria-busy", "true");
    boton.textContent = "Subiendo…";
  });
})();
