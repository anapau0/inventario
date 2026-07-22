from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ---------- Frontend ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- SCRUD: Productos ----------

# Search + Read (con parametro opcional ?buscar=)
@app.route("/api/productos", methods=["GET"])
def listar_productos():
    buscar = request.args.get("buscar", "").strip()
    conn = get_db()
    if buscar:
        like = f"%{buscar}%"
        filas = conn.execute(
            "SELECT * FROM productos WHERE nombre LIKE ? OR codigo LIKE ? ORDER BY id",
            (like, like),
        ).fetchall()
    else:
        filas = conn.execute("SELECT * FROM productos ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(f) for f in filas])


# Create
@app.route("/api/productos", methods=["POST"])
def crear_producto():
    data = request.get_json(force=True)
    codigo = (data.get("codigo") or "").strip()
    nombre = (data.get("nombre") or "").strip()
    stock = int(data.get("stock", 0) or 0)

    if not codigo or not nombre:
        return jsonify({"error": "Código y nombre son obligatorios"}), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO productos (codigo, nombre, stock) VALUES (?, ?, ?)",
        (codigo, nombre, stock),
    )
    conn.commit()
    nuevo_id = cur.lastrowid
    fila = conn.execute("SELECT * FROM productos WHERE id = ?", (nuevo_id,)).fetchone()
    conn.close()
    return jsonify(dict(fila)), 201


# Update general (editar código/nombre/stock manualmente)
@app.route("/api/productos/<int:producto_id>", methods=["PUT"])
def actualizar_producto(producto_id):
    data = request.get_json(force=True)
    conn = get_db()
    fila = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if fila is None:
        conn.close()
        return jsonify({"error": "Producto no encontrado"}), 404

    codigo = data.get("codigo", fila["codigo"])
    nombre = data.get("nombre", fila["nombre"])
    stock = data.get("stock", fila["stock"])

    conn.execute(
        "UPDATE productos SET codigo = ?, nombre = ?, stock = ? WHERE id = ?",
        (codigo, nombre, stock, producto_id),
    )
    conn.commit()
    fila = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    conn.close()
    return jsonify(dict(fila))


# Update rápido: botón "+"
@app.route("/api/productos/<int:producto_id>/incrementar", methods=["PUT"])
def incrementar_stock(producto_id):
    conn = get_db()
    fila = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if fila is None:
        conn.close()
        return jsonify({"error": "Producto no encontrado"}), 404

    conn.execute("UPDATE productos SET stock = stock + 1 WHERE id = ?", (producto_id,))
    conn.commit()
    fila = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    conn.close()
    return jsonify(dict(fila))


# Update rápido: botón "-"
@app.route("/api/productos/<int:producto_id>/decrementar", methods=["PUT"])
def decrementar_stock(producto_id):
    conn = get_db()
    fila = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if fila is None:
        conn.close()
        return jsonify({"error": "Producto no encontrado"}), 404

    if fila["stock"] > 0:
        conn.execute("UPDATE productos SET stock = stock - 1 WHERE id = ?", (producto_id,))
        conn.commit()

    fila = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    conn.close()
    return jsonify(dict(fila))


# Delete
@app.route("/api/productos/<int:producto_id>", methods=["DELETE"])
def eliminar_producto(producto_id):
    conn = get_db()
    conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)