/* Menú lateral en el teléfono (menos de 1024 px): botón «Menú», velo y tecla Escape.
   En pantallas anchas el menú queda fijo y este script no hace nada visible.

   Se carga sin defer en <head> para marcar <html> con .menu-js antes de dibujar: así el
   CSS esconde el menú fuera de la pantalla solo cuando hay JavaScript. Sin JavaScript,
   el menú se muestra arriba del contenido y el botón no aparece. */
(function () {
  "use strict";

  var raiz = document.documentElement;
  raiz.classList.add("menu-js");

  document.addEventListener("DOMContentLoaded", function () {
    var boton = document.querySelector("[data-menu-boton]");
    var menu = document.getElementById("menu-lateral");
    var velo = document.querySelector("[data-menu-velo]");
    var contenido = document.getElementById("contenido");
    if (!boton || !menu) {
      return;
    }
    var movil = window.matchMedia("(max-width: 1023.98px)");

    function abierto() {
      return raiz.classList.contains("menu-abierto");
    }

    function abrir() {
      raiz.classList.add("menu-abierto");
      boton.setAttribute("aria-expanded", "true");
      if (velo) {
        velo.hidden = false;
      }
      // El contenido de atrás no recibe foco ni lo lee el lector de pantalla mientras el menú está abierto.
      if (contenido) {
        contenido.inert = true;
      }
      var actual = menu.querySelector('[aria-current="page"]') || menu.querySelector("a, summary, button");
      if (actual) {
        actual.focus();
      }
    }

    function cerrar(devolverFoco) {
      if (!abierto()) {
        return;
      }
      raiz.classList.remove("menu-abierto");
      boton.setAttribute("aria-expanded", "false");
      if (velo) {
        velo.hidden = true;
      }
      if (contenido) {
        contenido.inert = false;
      }
      if (devolverFoco) {
        boton.focus();
      }
    }

    boton.addEventListener("click", function () {
      if (abierto()) {
        cerrar(true);
      } else {
        abrir();
      }
    });

    if (velo) {
      velo.addEventListener("click", function () {
        cerrar(true);
      });
    }

    document.addEventListener("keydown", function (evento) {
      if (evento.key === "Escape" && abierto()) {
        cerrar(true);
      }
    });

    // Al elegir un enlace (también los que llevan a una sección de la misma página) el menú se cierra.
    menu.addEventListener("click", function (evento) {
      if (movil.matches && evento.target.closest("a")) {
        cerrar(false);
      }
    });

    // Al pasar a pantalla ancha el menú queda fijo: se limpia el estado del teléfono.
    movil.addEventListener("change", function (evento) {
      if (!evento.matches) {
        cerrar(false);
      }
    });
  });
})();
