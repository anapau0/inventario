from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")

# Si existen estas variables de entorno (configuradas en Render), se conecta
# a Turso (base de datos persistente en la nube). Si no existen, usa un
# archivo SQLite local — útil para probar en tu computadora sin necesitar Turso.
TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

_conn = None


def get_db():
    """Reutiliza una única conexión durante toda la vida del proceso.
    Crear una conexión nueva por cada petición agota memoria/hilos en
    planes gratuitos (esto causaba los errores 502 y OOM en Render)."""
    global _conn
    if _conn is not None:
        return _conn

    if TURSO_URL:
        import libsql
        _conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
    else:
        import sqlite3
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    return _conn


def fila_a_dict(cursor, fila):
    """Convierte una fila (tupla) en diccionario usando los nombres de columna."""
    columnas = [d[0] for d in cursor.description]
    return dict(zip(columnas, fila))


def filas_a_dicts(cursor, filas):
    return [fila_a_dict(cursor, f) for f in filas]


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
        cur = conn.execute(
            "SELECT * FROM productos WHERE nombre LIKE ? OR codigo LIKE ? ORDER BY id",
            (like, like),
        )
    else:
        cur = conn.execute("SELECT * FROM productos ORDER BY id")
    resultado = filas_a_dicts(cur, cur.fetchall())
    return jsonify(resultado)


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
        "INSERT INTO productos (codigo, nombre, stock) VALUES (?, ?, ?) RETURNING id",
        (codigo, nombre, stock),
    )
    nuevo_id = cur.fetchone()[0]
    conn.commit()
    cur = conn.execute("SELECT * FROM productos WHERE id = ?", (nuevo_id,))
    fila = fila_a_dict(cur, cur.fetchone())
    return jsonify(fila), 201


# Update general (editar código/nombre/stock manualmente)
@app.route("/api/productos/<int:producto_id>", methods=["PUT"])
def actualizar_producto(producto_id):
    data = request.get_json(force=True)
    conn = get_db()
    cur = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    row = cur.fetchone()
    if row is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    actual = fila_a_dict(cur, row)

    codigo = data.get("codigo", actual["codigo"])
    nombre = data.get("nombre", actual["nombre"])
    stock = data.get("stock", actual["stock"])

    conn.execute(
        "UPDATE productos SET codigo = ?, nombre = ?, stock = ? WHERE id = ?",
        (codigo, nombre, stock, producto_id),
    )
    conn.commit()
    cur = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    fila = fila_a_dict(cur, cur.fetchone())
    return jsonify(fila)


# Update rápido: botón "+"
@app.route("/api/productos/<int:producto_id>/incrementar", methods=["PUT"])
def incrementar_stock(producto_id):
    conn = get_db()
    cur = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    row = cur.fetchone()
    if row is None:
        return jsonify({"error": "Producto no encontrado"}), 404

    conn.execute("UPDATE productos SET stock = stock + 1 WHERE id = ?", (producto_id,))
    conn.commit()
    cur = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    fila = fila_a_dict(cur, cur.fetchone())
    return jsonify(fila)


# Update rápido: botón "-"
@app.route("/api/productos/<int:producto_id>/decrementar", methods=["PUT"])
def decrementar_stock(producto_id):
    conn = get_db()
    cur = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    row = cur.fetchone()
    if row is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    actual = fila_a_dict(cur, row)

    if actual["stock"] > 0:
        conn.execute("UPDATE productos SET stock = stock - 1 WHERE id = ?", (producto_id,))
        conn.commit()

    cur = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    fila = fila_a_dict(cur, cur.fetchone())
    return jsonify(fila)


# Delete
@app.route("/api/productos/<int:producto_id>", methods=["DELETE"])
def eliminar_producto(producto_id):
    conn = get_db()
    conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)