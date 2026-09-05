/*
  Agregar al carrito.

  Sin JS el formulario se envía normal y la vista redirige al carrito. Con JS
  se manda por fetch y la pieza "viaja" hasta el contador del encabezado: el
  contador está lejos del botón, así que sin ese recorrido el número cambia
  donde nadie está mirando.
*/
(() => {
  "use strict";

  const leerCurva = (nombre, respaldo) =>
    getComputedStyle(document.documentElement).getPropertyValue(nombre).trim() || respaldo;

  const CURVA_RECORRIDO = leerCurva("--ease-recorrido", "cubic-bezier(0.77, 0, 0.175, 1)");
  const CURVA_SALIDA = leerCurva("--ease-salida", "cubic-bezier(0.23, 1, 0.32, 1)");

  // El vuelo cruza la pantalla entera. Por debajo de unos 400 ms el ojo no
  // alcanza a seguirlo y se pierde justo lo que la animación explica.
  const DURACION_DEL_VUELO = 420;
  const DURACION_DEL_LATIDO = 160;

  const prefiereMenosMovimiento = () =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const contador = document.querySelector("[data-contador-del-carrito]");
  const enlaceDelCarrito = document.querySelector("[data-enlace-del-carrito]");

  let latidoEnCurso = null;

  function actualizarContador(unidades) {
    if (!contador) return;
    contador.textContent = unidades > 0 ? ` (${unidades})` : "";

    // Se cancela el anterior en vez de encolarlo: si alguien agrega dos veces
    // seguidas, el segundo latido arranca desde donde iba el primero.
    if (latidoEnCurso) latidoEnCurso.cancel();

    if (prefiereMenosMovimiento()) {
      latidoEnCurso = contador.animate(
        [{ opacity: 0.35 }, { opacity: 1 }],
        { duration: 200, easing: CURVA_SALIDA }
      );
      return;
    }

    latidoEnCurso = contador.animate(
      [
        { transform: "scale(1)" },
        { transform: "scale(1.28)" },
        { transform: "scale(1)" },
      ],
      { duration: DURACION_DEL_LATIDO, easing: CURVA_SALIDA }
    );
  }

  function volarHastaElCarrito(imagen) {
    if (!imagen || !enlaceDelCarrito || prefiereMenosMovimiento()) return null;

    const origen = imagen.getBoundingClientRect();
    const destino = enlaceDelCarrito.getBoundingClientRect();
    if (!origen.width || !destino.width) return null;

    const clon = imagen.cloneNode(true);
    Object.assign(clon.style, {
      position: "fixed",
      left: `${origen.left}px`,
      top: `${origen.top}px`,
      width: `${origen.width}px`,
      height: `${origen.height}px`,
      margin: "0",
      objectFit: "cover",
      pointerEvents: "none",
      zIndex: "60",
      willChange: "transform, opacity",
    });
    document.body.appendChild(clon);

    const desplazamientoX =
      destino.left + destino.width / 2 - (origen.left + origen.width / 2);
    const desplazamientoY =
      destino.top + destino.height / 2 - (origen.top + origen.height / 2);

    const vuelo = clon.animate(
      [
        { transform: "translate(0px, 0px) scale(1)", opacity: 0.95 },
        {
          // Un arco corto: sube un poco antes de caer sobre el contador.
          transform: `translate(${desplazamientoX * 0.55}px, ${
            desplazamientoY * 0.35 - 40
          }px) scale(0.55)`,
          opacity: 0.9,
        },
        {
          transform: `translate(${desplazamientoX}px, ${desplazamientoY}px) scale(0.2)`,
          opacity: 0,
        },
      ],
      { duration: DURACION_DEL_VUELO, easing: CURVA_RECORRIDO, fill: "forwards" }
    );

    vuelo.finished.catch(() => {}).finally(() => clon.remove());
    return vuelo;
  }

  document.querySelectorAll("[data-agregar-al-carrito]").forEach((formulario) => {
    formulario.addEventListener("submit", async (evento) => {
      if (typeof window.fetch !== "function") return;
      evento.preventDefault();

      const aviso = document.querySelector("[data-aviso-del-carrito]");
      const imagen = document.querySelector("[data-foto-principal] img");
      const vuelo = volarHastaElCarrito(imagen);

      let datos;
      try {
        const respuesta = await fetch(formulario.action, {
          method: "POST",
          body: new FormData(formulario),
          headers: { "X-Peticion-Asincrona": "1" },
          credentials: "same-origin",
        });
        if (!respuesta.ok) throw new Error(`respuesta ${respuesta.status}`);
        datos = await respuesta.json();
      } catch (error) {
        // Si el fetch falla, se cae al envío de siempre y la vista redirige.
        formulario.submit();
        return;
      }

      // El número cambia cuando la pieza llega, no antes.
      if (vuelo) await vuelo.finished.catch(() => {});
      actualizarContador(datos.unidades);
      if (aviso) aviso.textContent = datos.aviso;
    });
  });
})();
