# Inventario y Ventas

Sistema de gestión de inventario y ventas desarrollado en Django.

## Estructura del Proyecto

- **administracion/**: Gestión de productos, categorías y empresas.
- **core/**: Funciones y vistas centrales.
- **inventario/**: Configuración principal del proyecto.
- **login/**: Autenticación de usuarios.
- **trabajadores/**: Gestión de ventas y trabajadores.
- **media/**: Archivos subidos por los usuarios.
- **static/**: Archivos estáticos (CSS, JS, imágenes).

## Requisitos

- Python 3.10+
- Django 5.1.6
- Pillow

Instala las dependencias con:

```sh
pip install -r requirements.txt
```

## Configuración

1. Realiza las migraciones:

```sh
python manage.py migrate
```

3. Crea un superusuario para acceder al admin:

```sh
python manage.py createsuperuser
```

4. Ejecuta el servidor de desarrollo:

```sh
python manage.py runserver
```
5. Crea un grupo llamado "Tabajadores":

```sh
en el admin /admin/
```
## Uso

- Accede al panel de administración en `/admin/`.
- El sistema permite gestionar productos, categorías, ventas y usuarios.
- Los archivos estáticos y de medios se sirven automáticamente en desarrollo.



## Notas

- No uses el servidor de desarrollo para producción.
- Para servir archivos estáticos y de medios en producción, usa un servidor web como Nginx o Apache.

---

### Estructura de carpetas

Consulta la estructura en este repositorio para más detalles.

---
