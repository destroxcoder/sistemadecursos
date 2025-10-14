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

3. Ejecuta la aplicación (por defecto se expone en `http://127.0.0.1:5000`):

   ```bash
   flask --app app run --debug
   ```

4. Abre el navegador y visita la ruta base para acceder a las vistas públicas.

Al iniciarse por primera vez se crea una base de datos SQLite (`sistemadecursos.db`) y un usuario administrador por defecto con el código `admin123`.

Los certificados subidos se almacenan en la carpeta `uploaded_certificates/` y se entregan mediante una URL segura.

## Cómo probar el sistema rápidamente

1. **Registrar un alumno:** ingresa a `http://127.0.0.1:5000/registro`, completa el formulario y guarda. Serás redirigido al inicio de sesión.
2. **Acceder como alumno:** en `http://127.0.0.1:5000/acceso` selecciona "Soy Alumno", escribe el DNI registrado y entra al portal donde se listan tus cursos.
3. **Acceder como administrador:** en la misma página selecciona "Administrador" e introduce el código `admin123` (o el configurado en `DEFAULT_ADMIN_CODE`).
4. **Crear datos de ejemplo:** desde el panel administrativo puedes registrar alumnos, crear cursos y asignar certificados PDF para verificar el flujo completo.

Si deseas que la aplicación esté disponible en tu red local, ejecuta `flask --app app run --host 0.0.0.0 --port 5000` y accede usando la IP de tu máquina.

## Estructura principal

- `app.py`: aplicación Flask con rutas de alumno y administrador.
- `templates/`: vistas HTML (registro, acceso, portal alumno, panel admin).
- `static/css/`: estilos personalizados.
- `uploaded_certificates/`: almacenamiento de certificados PDF.

## Configuración opcional

- Variable de entorno `SECRET_KEY` para la sesión de Flask.
- Variable de entorno `DEFAULT_ADMIN_CODE` para establecer otro código inicial de administrador.
