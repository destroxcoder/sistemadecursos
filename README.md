# Sistema de Gestión de Certificados

Aplicación web construida con Flask que permite gestionar alumnos, cursos e inscripciones para la emisión de certificados académicos. Incluye portal público para estudiantes y panel privado para administradores.

## Requisitos

- Python 3.10+
- pip

## Instalación y uso

1. Crea y activa un entorno virtual opcional.
2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación:

   ```bash
   flask --app app run --debug
   ```

4. Abre [http://127.0.0.1:5000](http://127.0.0.1:5000) en tu navegador.

Al iniciarse por primera vez se crea una base de datos SQLite (`sistemadecursos.db`) y un usuario administrador por defecto con el código `admin123`.

Los certificados subidos se almacenan en la carpeta `uploaded_certificates/` y se entregan mediante una URL segura.

## Estructura principal

- `app.py`: aplicación Flask con rutas de alumno y administrador.
- `templates/`: vistas HTML (registro, acceso, portal alumno, panel admin).
- `static/css/`: estilos personalizados.
- `uploaded_certificates/`: almacenamiento de certificados PDF.

## Configuración opcional

- Variable de entorno `SECRET_KEY` para la sesión de Flask.
- Variable de entorno `DEFAULT_ADMIN_CODE` para establecer otro código inicial de administrador.
