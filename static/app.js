const tbody = document.getElementById("tbody-productos");
const formNuevo = document.getElementById("form-nuevo");
const inputBuscar = document.getElementById("buscar");

async function cargarProductos(filtro = "") {
  const url = filtro ? `/api/productos?buscar=${encodeURIComponent(filtro)}` : "/api/productos";
  const res = await fetch(url);
  const productos = await res.json();
  renderTabla(productos);
}

function renderTabla(productos) {
  tbody.innerHTML = "";
  productos.forEach((p) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.codigo}</td>
      <td>${p.nombre}</td>
      <td>
        <button class="btn-stock btn-menos" data-id="${p.id}" data-accion="decrementar">−</button>
        <span class="stock-num">${p.stock}</span>
        <button class="btn-stock btn-mas" data-id="${p.id}" data-accion="incrementar">+</button>
      </td>
      <td>
        <button class="btn-eliminar" data-id="${p.id}" data-accion="eliminar">Eliminar</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Crear producto
formNuevo.addEventListener("submit", async (e) => {
  e.preventDefault();
  const codigo = document.getElementById("codigo").value.trim();
  const nombre = document.getElementById("nombre").value.trim();
  const stock = parseInt(document.getElementById("stock").value || "0", 10);

  await fetch("/api/productos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ codigo, nombre, stock }),
  });

  formNuevo.reset();
  document.getElementById("stock").value = 0;
  cargarProductos(inputBuscar.value);
});

// Botones +, -, eliminar (delegación de eventos)
tbody.addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;

  const id = btn.dataset.id;
  const accion = btn.dataset.accion;

  if (accion === "incrementar" || accion === "decrementar") {
    await fetch(`/api/productos/${id}/${accion}`, { method: "PUT" });
  } else if (accion === "eliminar") {
    if (!confirm("¿Eliminar este producto?")) return;
    await fetch(`/api/productos/${id}`, { method: "DELETE" });
  }

  cargarProductos(inputBuscar.value);
});

// Buscar en tiempo real
let timeoutBusqueda;
inputBuscar.addEventListener("input", () => {
  clearTimeout(timeoutBusqueda);
  timeoutBusqueda = setTimeout(() => cargarProductos(inputBuscar.value), 300);
});

cargarProductos();