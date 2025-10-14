import os
import sqlite3
from datetime import datetime
from flask import (
    Flask,
    flash,
    g,
    jsonify,
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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -------------------------
# Database helpers
# -------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
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
            horas_lectivas INTEGER NOT NULL DEFAULT 0,
            horas_academicas INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """
    )

    cursor.execute("PRAGMA table_info(cursos)")
    columnas_cursos = {col["name"] for col in cursor.fetchall()}
    if "horas_lectivas" not in columnas_cursos:
        cursor.execute(
            "ALTER TABLE cursos ADD COLUMN horas_lectivas INTEGER NOT NULL DEFAULT 0"
        )
        cursor.execute("UPDATE cursos SET horas_lectivas = horas WHERE horas_lectivas = 0")
    if "horas_academicas" not in columnas_cursos:
        cursor.execute(
            "ALTER TABLE cursos ADD COLUMN horas_academicas INTEGER NOT NULL DEFAULT 0"
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


@app.context_processor
def inject_datetime():
    return {"datetime": datetime}


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


def wants_json_response() -> bool:
    accept_header = request.headers.get("Accept", "")
    return "application/json" in accept_header or request.is_json


def serialize_row(row):
    return dict(row) if row is not None else None


def obtener_alumnos(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM alumnos ORDER BY created_at DESC")
    return [serialize_row(row) for row in cursor.fetchall()]


def obtener_cursos(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM cursos ORDER BY created_at DESC")
    return [serialize_row(row) for row in cursor.fetchall()]


def obtener_inscripciones(db):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT i.*, a.nombre AS alumno_nombre, c.nombre AS curso_nombre,
               c.horas_lectivas, c.horas_academicas, c.horas AS curso_horas, c.creditos
        FROM inscripciones i
        JOIN alumnos a ON a.id = i.fk_alumno_id
        JOIN cursos c ON c.id = i.fk_curso_id
        ORDER BY i.created_at DESC
        """
    )
    return [serialize_row(row) for row in cursor.fetchall()]


def obtener_inscripcion_por_id(db, inscripcion_id):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT i.*, a.nombre AS alumno_nombre, c.nombre AS curso_nombre,
               c.horas_lectivas, c.horas_academicas, c.horas AS curso_horas, c.creditos
        FROM inscripciones i
        JOIN alumnos a ON a.id = i.fk_alumno_id
        JOIN cursos c ON c.id = i.fk_curso_id
        WHERE i.id = ?
        """,
        (inscripcion_id,),
    )
    return serialize_row(cursor.fetchone())


def obtener_alumno_por_id(db, alumno_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,))
    return serialize_row(cursor.fetchone())


def obtener_curso_por_id(db, curso_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM cursos WHERE id = ?", (curso_id,))
    return serialize_row(cursor.fetchone())


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
               c.horas, c.creditos, c.horas_lectivas, c.horas_academicas
        FROM inscripciones i
        JOIN cursos c ON c.id = i.fk_curso_id
        WHERE i.fk_alumno_id = ?
        ORDER BY i.created_at DESC
        """,
        (alumno_id,),
    )
    cursos = [dict(row) for row in cursor.fetchall()]
    cursos_finalizados = sum(1 for curso in cursos if curso.get("estado") == "Finalizado")

    return render_template(
        "portal_alumno.html",
        alumno_nombre=session.get("alumno_nombre"),
        cursos=cursos,
        cursos_finalizados=cursos_finalizados,
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
    data = {
        "alumnos": obtener_alumnos(db),
        "cursos": obtener_cursos(db),
        "inscripciones": obtener_inscripciones(db),
    }

    return render_template("panel_admin.html", initial_data=data)


@app.route("/admin/api/dashboard")
@requiere_admin
def api_dashboard():
    db = get_db()
    data = {
        "alumnos": obtener_alumnos(db),
        "cursos": obtener_cursos(db),
        "inscripciones": obtener_inscripciones(db),
    }
    return jsonify(data)


@app.route("/admin/alumnos", methods=["POST"])
@requiere_admin
def crear_alumno():
    data = request.get_json(silent=True) if request.is_json else request.form
    nombre = (data.get("nombre") or "").strip()
    dni = (data.get("dni") or "").strip()
    celular = (data.get("celular") or None) if data.get("celular") else None

    if not nombre or not dni:
        message = "El nombre y el DNI son obligatorios"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM alumnos WHERE dni = ?", (dni,))
    if cursor.fetchone():
        message = "El DNI ya está registrado"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    cursor.execute(
        "INSERT INTO alumnos (nombre, dni, celular, created_at) VALUES (?, ?, ?, ?)",
        (nombre, dni, celular, datetime.now().isoformat()),
    )
    db.commit()

    alumno = obtener_alumno_por_id(db, cursor.lastrowid)
    message = "Alumno registrado correctamente"
    if wants_json_response():
        return jsonify({"message": message, "alumno": alumno}), 201

    flash(message, "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/alumnos/<int:alumno_id>", methods=["POST", "PUT", "DELETE"])
@requiere_admin
def editar_alumno(alumno_id):
    db = get_db()
    cursor = db.cursor()

    if request.method == "DELETE":
        cursor.execute("DELETE FROM alumnos WHERE id = ?", (alumno_id,))
        db.commit()
        if cursor.rowcount == 0:
            message = "Alumno no encontrado"
            status = 404
        else:
            message = "Alumno eliminado"
            status = 200
        if wants_json_response():
            return jsonify({"message": message}), status
        flash(message, "success" if status == 200 else "danger")
        return redirect(url_for("panel_admin"))

    data = request.get_json(silent=True) if request.is_json else request.form
    nombre = (data.get("nombre") or "").strip()
    dni = (data.get("dni") or "").strip()
    celular = (data.get("celular") or None) if data.get("celular") else None

    if not nombre or not dni:
        message = "El nombre y el DNI son obligatorios"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    cursor.execute(
        "SELECT id FROM alumnos WHERE dni = ? AND id != ?",
        (dni, alumno_id),
    )
    if cursor.fetchone():
        message = "El DNI ya está registrado para otro alumno"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    cursor.execute(
        "UPDATE alumnos SET nombre = ?, dni = ?, celular = ? WHERE id = ?",
        (nombre, dni, celular, alumno_id),
    )
    db.commit()

    alumno = obtener_alumno_por_id(db, alumno_id)
    message = "Alumno actualizado"
    if wants_json_response():
        return jsonify({"message": message, "alumno": alumno}), 200

    flash(message, "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/cursos", methods=["POST"])
@requiere_admin
def crear_curso():
    data = request.get_json(silent=True) if request.is_json else request.form
    nombre = (data.get("nombre") or "").strip()
    horas_lectivas = data.get("horas_lectivas")
    horas_academicas = data.get("horas_academicas")
    creditos = data.get("creditos")

    if not nombre or horas_lectivas is None or horas_academicas is None or creditos is None:
        message = "Todos los campos del curso son obligatorios"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    try:
        horas_lectivas_val = max(0, int(horas_lectivas))
        horas_academicas_val = max(0, int(horas_academicas))
        creditos_val = max(0, int(creditos))
    except (TypeError, ValueError):
        message = "Las horas y los créditos deben ser números válidos"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    horas_totales = horas_lectivas_val + horas_academicas_val

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO cursos (
            nombre, horas, creditos, horas_lectivas, horas_academicas, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            nombre,
            horas_totales,
            creditos_val,
            horas_lectivas_val,
            horas_academicas_val,
            datetime.now().isoformat(),
        ),
    )
    db.commit()

    curso = obtener_curso_por_id(db, cursor.lastrowid)
    message = "Curso agregado"
    if wants_json_response():
        return jsonify({"message": message, "curso": curso}), 201

    flash(message, "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/cursos/<int:curso_id>", methods=["POST", "PUT", "DELETE"])
@requiere_admin
def editar_curso(curso_id):
    db = get_db()
    cursor = db.cursor()

    if request.method == "DELETE":
        cursor.execute("DELETE FROM cursos WHERE id = ?", (curso_id,))
        db.commit()
        if cursor.rowcount == 0:
            message = "Curso no encontrado"
            status = 404
        else:
            message = "Curso eliminado"
            status = 200
        if wants_json_response():
            return jsonify({"message": message}), status
        flash(message, "success" if status == 200 else "danger")
        return redirect(url_for("panel_admin"))

    data = request.get_json(silent=True) if request.is_json else request.form
    nombre = (data.get("nombre") or "").strip()
    horas_lectivas = data.get("horas_lectivas")
    horas_academicas = data.get("horas_academicas")
    creditos = data.get("creditos")

    if not nombre or horas_lectivas is None or horas_academicas is None or creditos is None:
        message = "Todos los campos son obligatorios"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    try:
        horas_lectivas_val = max(0, int(horas_lectivas))
        horas_academicas_val = max(0, int(horas_academicas))
        creditos_val = max(0, int(creditos))
    except (TypeError, ValueError):
        message = "Las horas y los créditos deben ser números válidos"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    horas_totales = horas_lectivas_val + horas_academicas_val

    cursor.execute(
        """
        UPDATE cursos
        SET nombre = ?, horas = ?, creditos = ?, horas_lectivas = ?, horas_academicas = ?
        WHERE id = ?
        """,
        (
            nombre,
            horas_totales,
            creditos_val,
            horas_lectivas_val,
            horas_academicas_val,
            curso_id,
        ),
    )
    db.commit()

    curso = obtener_curso_por_id(db, curso_id)
    message = "Curso actualizado"
    if wants_json_response():
        return jsonify({"message": message, "curso": curso}), 200

    flash(message, "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/inscripciones", methods=["POST"])
@requiere_admin
def crear_inscripcion():
    data = request.get_json(silent=True) if request.is_json else request.form
    alumno_id = data.get("alumno_id")
    curso_id = data.get("curso_id")
    numero_registro = (data.get("numero_registro") or "").strip()
    estado = data.get("estado", "En Curso")
    certificado_file = None if request.is_json else request.files.get("certificado")

    if alumno_id is None or curso_id is None or not numero_registro:
        message = "Debes completar todos los campos obligatorios"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    try:
        alumno_id_val = int(alumno_id)
        curso_id_val = int(curso_id)
    except (TypeError, ValueError):
        message = "Los identificadores de alumno y curso deben ser válidos"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    db = get_db()
    if not obtener_alumno_por_id(db, alumno_id_val) or not obtener_curso_por_id(
        db, curso_id_val
    ):
        message = "El alumno o el curso seleccionado no existe"
        if wants_json_response():
            return jsonify({"message": message}), 404
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

    certificado_url = guardar_certificado(certificado_file)

    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO inscripciones (
            fk_alumno_id, fk_curso_id, numero_registro, estado, certificado_url, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            alumno_id_val,
            curso_id_val,
            numero_registro,
            estado,
            certificado_url,
            datetime.now().isoformat(),
        ),
    )
    db.commit()

    inscripcion = obtener_inscripcion_por_id(db, cursor.lastrowid)
    message = "Inscripción creada"
    if wants_json_response():
        return jsonify({"message": message, "inscripcion": inscripcion}), 201

    flash(message, "success")
    return redirect(url_for("panel_admin"))


@app.route("/admin/inscripciones/<int:inscripcion_id>", methods=["POST", "PUT", "DELETE"])
@requiere_admin
def editar_inscripcion(inscripcion_id):
    db = get_db()
    cursor = db.cursor()

    if request.method == "DELETE":
        cursor.execute("DELETE FROM inscripciones WHERE id = ?", (inscripcion_id,))
        db.commit()
        if cursor.rowcount == 0:
            message = "Inscripción no encontrada"
            status = 404
        else:
            message = "Inscripción eliminada"
            status = 200
        if wants_json_response():
            return jsonify({"message": message}), status
        flash(message, "success" if status == 200 else "danger")
        return redirect(url_for("panel_admin"))

    data = request.get_json(silent=True) if request.is_json else request.form
    numero_registro = (data.get("numero_registro") or "").strip()
    estado = data.get("estado", "En Curso")
    certificado_file = None if request.is_json else request.files.get("certificado")

    if not numero_registro:
        message = "El número de registro es obligatorio"
        if wants_json_response():
            return jsonify({"message": message}), 400
        flash(message, "danger")
        return redirect(url_for("panel_admin"))

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

    inscripcion = obtener_inscripcion_por_id(db, inscripcion_id)
    message = "Inscripción actualizada"
    if wants_json_response():
        return jsonify({"message": message, "inscripcion": inscripcion}), 200

    flash(message, "success")
    return redirect(url_for("panel_admin"))


@app.route("/salir")
def salir():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("acceso"))


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
