# PASOS DE INSTALACIÓN

### CURSOS DE RESPALDO

| Nombre del Video | Enlace                                                                                    |
| ---------------- |-------------------------------------------------------------------------------------------|
| Curso de Python con Django de 0 a Máster | [Ver aquí](https://youtube.com/playlist?list=PLxm9hnvxnn-j5ZDOgQS63UIBxQytPdCG7 "Enlace") |
| Curso de Deploy de un Proyecto Django en un VPS Ubuntu | [Ver aquí](https://youtube.com/playlist?list=PLxm9hnvxnn-hFNSoNrWM0LalFnSv5oMas "Enlace")           |
| Curso de Python con Django Avanzado I | [Ver aquí](https://www.youtube.com/playlist?list=PLxm9hnvxnn-gvB0h0sEWjAf74ge4tkTOO "Enlace")       |
| Curso de Python con Django Avanzado II | [Ver aquí](https://www.youtube.com/playlist?list=PLxm9hnvxnn-jL7Fqr-GL2iSPfgJ99BhEC "Enlace")       |

### INSTALADORES

| Nombre        | Instalador                                                                                                                                                                                                                                           |
|:--------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| Compilador    | [Python3](https://www.python.org/downloads/release/python-31011/ "Python3")                                                                                                                                                                                                                                |
| IDE           | [Visual Studio Code](https://code.visualstudio.com/ "Visual Studio Code"), [Sublime Text](https://www.sublimetext.com/ "Sublime Text"), [Pycharm](https://www.jetbrains.com/es-es/pycharm/download/#section=windows "Pycharm")                       |
| Base de datos | [Sqlite Studio](https://github.com/pawelsalawa/sqlitestudio/releases "Sqlite Studio"), [PostgreSQL](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads "PostgreSQL"), [MySQL](https://www.apachefriends.org/es/index.html "MySQL") |

### INSTALACIÓN DEL PROYECTO

Clonamos el proyecto en nuestro directorio seleccionado

```bash
git clone URL
```

Creamos nuestro entorno virtual para poder instalar las librerías del proyecto

```bash
python3.10 -m venv venv o virtualenv venv -ppython3.10
source venv/bin/active
```

Instalamos el complemento para la librería WEASYPRINT

Si estas usando Windows debe descargar el complemento de [GTK3 installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases "GTK3 installer"). En algunas ocaciones se debe colocar en las variables de entorno como primera para que funcione y se debe reiniciar el computador.

Si estas usando Linux debes instalar las [librerias](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#linux "librerias") correspondientes a la distribución que tenga instalado en su computador.

Instalamos las librerías del proyecto

```bash
pip install -r deploy/txt/requirements.txt
```

Ejecutamos las migraciones para crear nuestra base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

Creamos los datos iniciales para iniciar nuestro proyecto

```bash
python manage.py start_installation
python manage.py insert_test_data (Opcional)
```

Iniciamos el servidor del proyecto

```bash
python manage.py runserver 0:8000 
username: admin
password: hacker94
```

# Gracias por adquirir mi producto ✅🙏

#### Esto me sirve mucho para seguir produciendo mi contenido 🤗​

### ¡Apóyame! para seguir haciéndolo siempre 😊👏

Paso la mayor parte de mi tiempo creando contenido y ayudando a futuros programadores sobre el desarrollo web con tecnología open source.

🤗💪¡Muchas Gracias!💪🤗

**Puedes apoyarme de la siguiente manera.**

**Suscribiéndote**
https://www.youtube.com/c/AlgoriSoft?sub_confirmation=1

**Siguiendo**
https://www.facebook.com/algorisoft

**Donando por PayPal**
williamjair94@hotmail.com

***AlgoriSoft te desea lo mejor en tu aprendizaje y crecimiento profesional como programador 🤓.***