import os
import sqlite3
from datetime import datetime
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

DATABASE = os.path.join(os.path.dirname(__file__), "sistemadecursos.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploaded_certificates")
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# -------------------------
# Database helpers
# -------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dni TEXT NOT NULL UNIQUE,
            celular TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS administradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            codigo_hash TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            horas INTEGER NOT NULL,
            creditos INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fk_alumno_id INTEGER NOT NULL,
            fk_curso_id INTEGER NOT NULL,
            numero_registro TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'En Curso',
            certificado_url TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (fk_alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
            FOREIGN KEY (fk_curso_id) REFERENCES cursos(id) ON DELETE CASCADE
        );
        """
    )

    # Create a default administrator if none exists
    cursor.execute("SELECT COUNT(*) as total FROM administradores")
    if cursor.fetchone()["total"] == 0:
        default_password = os.environ.get("DEFAULT_ADMIN_CODE", "admin123")
        cursor.execute(
            "INSERT INTO administradores (nombre, codigo_hash) VALUES (?, ?)",
            ("Administrador", generate_password_hash(default_password)),
        )
        print("Se creó un administrador por defecto con el código 'admin123'.")

    db.commit()


@app.before_request
def before_request():
    init_db()


# -------------------------
# Utilidades
# -------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def guardar_certificado(file_storage):
    if file_storage and allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file_storage.save(filepath)
        return url_for("descargar_certificado", filename=filename)
    return None


# -------------------------
# Rutas públicas
# -------------------------
@app.route("/")
def index():
    return redirect(url_for("acceso"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        dni = request.form.get("dni")
        celular = request.form.get("celular")

        if not nombre or not dni:
            flash("El nombre y el DNI son obligatorios", "danger")
            return redirect(url_for("registro"))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM alumnos WHERE dni = ?", (dni,))
        if cursor.fetchone():
            flash("El DNI ingresado ya está registrado.", "danger")
            return redirect(url_for("registro"))

        cursor.execute(
            "INSERT INTO alumnos (nombre, dni, celular, created_at) VALUES (?, ?, ?, ?)",
            (nombre, dni, celular, datetime.now().isoformat()),
        )
        db.commit()
        flash("Registro exitoso. Ahora puedes acceder con tu DNI.", "success")
        return redirect(url_for("acceso"))

    return render_template("registro.html")


@app.route("/acceso", methods=["GET", "POST"])
def acceso():
    if request.method == "POST":
        rol = request.form.get("rol")
        db = get_db()
        cursor = db.cursor()

        if rol == "alumno":
            dni = request.form.get("dni")
            cursor.execute("SELECT id, nombre FROM alumnos WHERE dni = ?", (dni,))
            alumno = cursor.fetchone()
            if alumno:
                session.clear()
                session["alumno_id"] = alumno["id"]
                session["alumno_nombre"] = alumno["nombre"]
                return redirect(url_for("portal_alumno"))
            flash("No encontramos un alumno con ese DNI.", "danger")
        elif rol == "admin":
            codigo = request.form.get("codigo")
            cursor.execute("SELECT id, codigo_hash FROM administradores")
            admins = cursor.fetchall()
            for admin in admins:
                if check_password_hash(admin["codigo_hash"], codigo):
                    session.clear()
                    session["admin_id"] = admin["id"]
                    return redirect(url_for("panel_admin"))
            flash("Código de acceso incorrecto.", "danger")
        else:
            flash("Selecciona un tipo de acceso válido.", "danger")

    return render_template("acceso.html")


@app.route("/portal-alumno")
def portal_alumno():
    alumno_id = session.get("alumno_id")
    if not alumno_id:
        return redirect(url_for("acceso"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT i.id, i.numero_registro, i.estado, i.certificado_url, c.nombre AS curso_nombre,
               c.horas, c.creditos
        FROM inscripciones i
        JOIN cursos c ON c.id = i.fk_curso_id
        WHERE i.fk_alumno_id = ?
        ORDER BY i.created_at DESC
        """,
        (alumno_id,),
    )
    cursos = cursor.fetchall()

    return render_template(
        "portal_alumno.html",
        alumno_nombre=session.get("alumno_nombre"),
        cursos=cursos,
    )


@app.route("/certificados/<filename>")
def descargar_certificado(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)


# -------------------------
# Rutas de administración
# -------------------------
def requiere_admin(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("acceso"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/panel-admin")
@requiere_admin
def panel_admin():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM alumnos ORDER BY created_at DESC")
    alumnos = cursor.fetchall()

    cursor.execute("SELECT * FROM cursos ORDER BY created_at DESC")
    cursos = cursor.fetchall()

    cursor.execute(
        """
        SELECT i.*, a.nombre AS alumno_nombre, c.nombre AS curso_nombre
        FROM inscripciones i
        JOIN alumnos a ON a.id = i.fk_alumno_id
        JOIN cursos c ON c.id = i.fk_curso_id
        ORDER BY i.created_at DESC
        """
    )
    inscripciones = cursor.fetchall()

    return render_template(
        "panel_admin.html",
        alumnos=alumnos,
        cursos=cursos,
        inscripciones=inscripciones,
    )


@app.route("/admin/alumnos", methods=["POST"])
@requiere_admin
def crear_alumno():
    nombre = request.form.get("nombre")
    dni = request.form.get("dni")
    celular = request.form.get("celular")
    if not nombre or not dni:
        flash("El nombre y el DNI son obligatorios", "danger")
        return redirect(url_for("panel_admin"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM alumnos WHERE dni = ?", (dni,))
    if cursor.fetchone():
        flash("El DNI ya está registrado", "danger")
        return redirect(url_for("panel_admin"))

    cursor.execute(
        "INSERT INTO alumnos (nombre, dni, celular, created_at) VALUES (?, ?, ?, ?)",
        (nombre, dni, celular, datetime.now().isoformat()),
    )
    db.commit()
    flash("Alumno registrado correctamente", "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/alumnos/<int:alumno_id>", methods=["POST"])
@requiere_admin
def editar_alumno(alumno_id):
    nombre = request.form.get("nombre")
    celular = request.form.get("celular")
    if not nombre:
        flash("El nombre es obligatorio", "danger")
        return redirect(url_for("panel_admin"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE alumnos SET nombre = ?, celular = ? WHERE id = ?",
        (nombre, celular, alumno_id),
    )
    db.commit()
    flash("Alumno actualizado", "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/cursos", methods=["POST"])
@requiere_admin
def crear_curso():
    nombre = request.form.get("nombre")
    horas = request.form.get("horas")
    creditos = request.form.get("creditos")
    if not nombre or not horas or not creditos:
        flash("Todos los campos del curso son obligatorios", "danger")
        return redirect(url_for("panel_admin"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO cursos (nombre, horas, creditos, created_at) VALUES (?, ?, ?, ?)",
        (nombre, int(horas), int(creditos), datetime.now().isoformat()),
    )
    db.commit()
    flash("Curso agregado", "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/cursos/<int:curso_id>", methods=["POST"])
@requiere_admin
def editar_curso(curso_id):
    nombre = request.form.get("nombre")
    horas = request.form.get("horas")
    creditos = request.form.get("creditos")
    if not nombre or not horas or not creditos:
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for("panel_admin"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE cursos SET nombre = ?, horas = ?, creditos = ? WHERE id = ?",
        (nombre, int(horas), int(creditos), curso_id),
    )
    db.commit()
    flash("Curso actualizado", "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/inscripciones", methods=["POST"])
@requiere_admin
def crear_inscripcion():
    alumno_id = request.form.get("alumno_id")
    curso_id = request.form.get("curso_id")
    numero_registro = request.form.get("numero_registro")
    estado = request.form.get("estado", "En Curso")
    certificado_file = request.files.get("certificado")

    if not alumno_id or not curso_id or not numero_registro:
        flash("Debes completar todos los campos obligatorios", "danger")
        return redirect(url_for("panel_admin"))

    certificado_url = guardar_certificado(certificado_file)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO inscripciones (
            fk_alumno_id, fk_curso_id, numero_registro, estado, certificado_url, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            int(alumno_id),
            int(curso_id),
            numero_registro,
            estado,
            certificado_url,
            datetime.now().isoformat(),
        ),
    )
    db.commit()
    flash("Inscripción creada", "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/inscripciones/<int:inscripcion_id>", methods=["POST"])
@requiere_admin
def editar_inscripcion(inscripcion_id):
    numero_registro = request.form.get("numero_registro")
    estado = request.form.get("estado", "En Curso")
    certificado_file = request.files.get("certificado")

    db = get_db()
    cursor = db.cursor()

    certificado_url = None
    if certificado_file and certificado_file.filename:
        certificado_url = guardar_certificado(certificado_file)

    if certificado_url:
        cursor.execute(
            """
            UPDATE inscripciones
            SET numero_registro = ?, estado = ?, certificado_url = ?
            WHERE id = ?
            """,
            (numero_registro, estado, certificado_url, inscripcion_id),
        )
    else:
        cursor.execute(
            """
            UPDATE inscripciones
            SET numero_registro = ?, estado = ?
            WHERE id = ?
            """,
            (numero_registro, estado, inscripcion_id),
        )

    db.commit()
    flash("Inscripción actualizada", "success")
    return redirect(url_for("panel_admin"))


@app.route("/salir")
def salir():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("acceso"))


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
