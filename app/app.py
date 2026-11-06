import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.secret_key = "clave_de_pruebas_tfg"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not username or not password:
            flash("Debes introducir usuario y contraseña.")
            return redirect(url_for("register"))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, "user"),
        )
        conn.commit()
        conn.close()

        flash("Usuario registrado correctamente. Ya puedes iniciar sesión.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # VULNERABILIDAD DELIBERADA: SQL Injection.
        # La consulta se construye concatenando directamente los datos introducidos.
        query = (
            "SELECT * FROM users WHERE username = '"
            + username
            + "' AND password = '"
            + password
            + "'"
        )

        conn = get_db_connection()
        user = conn.execute(query).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Sesión iniciada correctamente.")
            return redirect(url_for("profile"))

        flash("Credenciales incorrectas.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("index"))


@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Debes iniciar sesión para acceder al perfil.")
        return redirect(url_for("login"))

    return render_template("profile.html")


@app.route("/comments", methods=["GET", "POST"])
def comments():
    if "user_id" not in session:
        flash("Debes iniciar sesión para ver o publicar comentarios.")
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        content = request.form.get("content", "")
        if content:
            conn.execute(
                "INSERT INTO comments (user_id, content) VALUES (?, ?)",
                (session["user_id"], content),
            )
            conn.commit()
            flash("Comentario publicado.")
        return redirect(url_for("comments"))

    comment_list = conn.execute(
        """
        SELECT comments.id, comments.content, comments.created_at, users.username
        FROM comments
        JOIN users ON comments.user_id = users.id
        ORDER BY comments.created_at DESC
        """
    ).fetchall()
    conn.close()

    return render_template("comments.html", comments=comment_list)


@app.route("/search")
def search():
    q = request.args.get("q", "")

    # VULNERABILIDAD DELIBERADA: XSS reflejado.
    # El valor de q se inserta directamente en la respuesta HTML sin escaparlo.
    return f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Búsqueda</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <main class="container">
            <h1>Resultados de búsqueda</h1>
            <p>Has buscado: {q}</p>
            <form action="/search" method="get">
                <input type="text" name="q" placeholder="Buscar" value="{q}">
                <button type="submit">Buscar</button>
            </form>
            <p><a href="/">Volver al inicio</a></p>
        </main>
    </body>
    </html>
    """


@app.route("/admin")
def admin():
    # VULNERABILIDAD DELIBERADA: control de acceso roto.
    # No se comprueba si el usuario ha iniciado sesión ni si tiene rol de administrador.
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users ORDER BY id").fetchall()
    conn.close()
    return render_template("admin.html", users=users)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
