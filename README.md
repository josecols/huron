Hurón
=====

Hurón es un script para descargar listas de reproducción desde 8tracks. Debido a cambios en la API, después de la tercera canción se debe esperar un tiempo para que la solicitud no sea reconocida como un `skip`.

Dependencias
------------
Este script depende de dos librerías [requests](https://pypi.python.org/pypi/requests) y [mutagen](https://pypi.python.org/pypi/mutagen).

Utilización
-----------

Para utilizar el script simplemente se debe ejecutar desde la línea de comando: `python huron.py <url_playlist>`. Dónde `<url_playlist>` es la URL del playlist en 8tracks, incluyendo `http://`.

También se puede ejecutar simplemente `python huron.py`, el script solicitará la URL por la línea de comando.

josecolsg@gmail.com

