# Sistema de Gestión de Certificados

Aplicación web construida con Flask que permite gestionar alumnos, cursos e inscripciones para la emisión de certificados académicos. Incluye portal público para estudiantes y panel privado para administradores.

## Requisitos

- Python 3.10+
- pip

## Instalación y uso en local

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

## Despliegue paso a paso

### 1. Prepara el repositorio en GitHub

1. Crea un repositorio vacío llamado, por ejemplo, `sistemadecursos` en tu cuenta de GitHub.
2. En tu máquina local inicializa Git (si todavía no lo hiciste):

   ```bash
   git init
   git add .
   git commit -m "Inicializa sistema de certificados"
   ```

3. Agrega el remoto y sube el código:

   ```bash
   git remote add origin https://github.com/<TU_USUARIO>/sistemadecursos.git
   git branch -M main
   git push -u origin main
   ```

> 💡 No subas `sistemadecursos.db` si ya existe; puedes agregarlo al `.gitignore` para mantener privados tus datos.

### 2. Despliegue en Render (opción recomendada para empezar)

1. Crea una cuenta en [https://render.com](https://render.com) e inicia sesión.
2. En el panel de Render haz clic en **New** → **Web Service** y conecta tu cuenta de GitHub.
3. Autoriza el acceso a tu repositorio `sistemadecursos` y selecciónalo.
4. Configura el servicio con los siguientes valores:

   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `flask --app app run --host 0.0.0.0 --port 10000`
   - **Region:** la más cercana a tus usuarios

   Render detecta automáticamente que la aplicación escucha en el puerto `10000` (configúralo en la sección _Advanced_ si es necesario).

5. En la sección **Environment** agrega, si lo deseas, variables como `SECRET_KEY` y `DEFAULT_ADMIN_CODE`.
6. Haz clic en **Create Web Service**. Render clonará el repositorio, instalará las dependencias y lanzará la aplicación. El primer despliegue puede tardar varios minutos.
7. Cuando el estado pase a **Live**, verás una URL pública similar a `https://sistemadecursos.onrender.com`. Úsala para acceder al sistema.

Para futuros cambios, solo haz `git push` a la rama principal; Render desplegará automáticamente la versión más reciente.

### 3. Despliegue en Railway (alternativa rápida)

1. Regístrate en [https://railway.app](https://railway.app) y entra al panel.
2. Selecciona **New Project** → **Deploy from GitHub repo** y autoriza el acceso a tu repositorio `sistemadecursos`.
3. Railway detectará que es una aplicación Flask y configurará la imagen automáticamente. Si usas SQLite no necesitas pasos adicionales.
4. En la pestaña **Variables** puedes definir `SECRET_KEY`, `DEFAULT_ADMIN_CODE` u otras variables.
5. Al finalizar el despliegue obtendrás una URL pública del tipo `https://sistemadecursos-production.up.railway.app`.

### 4. Otras opciones de despliegue

Si necesitas mayor control o escalar el proyecto, evalúa estas alternativas:

- **Google Cloud Run** o **AWS Elastic Beanstalk** utilizando un contenedor Docker con Gunicorn.
- **Microsoft Azure App Service** con un _startup command_ similar al de Render.
- **Vercel** empleando un adaptador WSGI como `vercel-python-wsgi`.

En todos los casos asegúrate de:

- Mantener `SECRET_KEY` y `DEFAULT_ADMIN_CODE` como variables de entorno.
- Configurar el puerto y host de escucha según los requisitos del proveedor.
- Servir los certificados desde un almacenamiento seguro (puede ser un bucket en la nube si tu proveedor no permite escritura en disco).

## Estructura principal

- `app.py`: aplicación Flask con rutas de alumno y administrador.
- `templates/`: vistas HTML (registro, acceso, portal alumno, panel admin).
- `static/css/`: estilos personalizados.
- `uploaded_certificates/`: almacenamiento de certificados PDF.

## Configuración opcional

- Variable de entorno `SECRET_KEY` para la sesión de Flask.
- Variable de entorno `DEFAULT_ADMIN_CODE` para establecer otro código inicial de administrador.
