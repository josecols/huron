Hurón
=====

Hurón es un script para descargar listas de reproducción desde 8tracks. Debido a cambios en la API, después de la tercera canción se debe esperar un tiempo para que la solicitud no sea reconocida como un `skip`. El script se encarga automáticamente de asignar las etiquetas título, álbum, artista, año, género y albumart utilizando [Discogs](http://www.discogs.com/) y [Soundcloud](https://soundcloud.com/).

Dependencias
------------
Este script depende de dos librerías [requests](https://pypi.python.org/pypi/requests) y [mutagen](https://pypi.python.org/pypi/mutagen). También depende de la utilidad [ffmpeg](http://www.ffmpeg.org/) para realizar la conversión de todas las canciones a MP3.

Distribución
------------
En la carpeta [dist](https://github.com/josecols/huron/tree/master/dist) se encuentra la distribución para Windows. Para utilizarla se debe ejecutar `huron.exe` e ingresar la URL de la lista de reproducción en 8tracks.

Utilización
-----------

Para utilizar el script simplemente se debe ejecutar desde la línea de comando: `python huron.py <url_playlist>`. Dónde `<url_playlist>` es la URL del playlist en 8tracks, incluyendo `http://`.

También se puede ejecutar simplemente `python huron.py`, el script solicitará la URL por la línea de comando.

josecolsg@gmail.com

<p align="center"><img src="https://raw.githubusercontent.com/josecols/huron/master/huron/huron.png" alt="Hurón" width="164"/></p>
