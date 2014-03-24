#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import os
import sys
import time
import mutagen.id3
from mutagen.mp3 import MP3

API_KEY = 'ba584160f1b8564f82d78529eada82179edc0fbb'
API_VERSION = 3


class Cancion:

    def __init__(
        self,
        cancion_id,
        nombre,
        album,
        fecha,
        artista,
        url,
        archivo,
        ):

        self.id = cancion_id
        self.nombre = nombre
        self.album = album
        self.fecha = fecha
        self.artista = artista
        self.url = url
        self.archivo = archivo

    def __unicode__(self):
        return self.nombre

    def __str__(self):
        return self.nombre
    
    
class Mix:

    def __init__(
        self,
        nombre,
        mix_id,
        canciones,
        cover,
        ):

        self.nombre = nombre
        self.id = mix_id
        self.canciones = canciones
        self.cover = cover
        self.cover_archivo = None

    def __del__(self):
        try:
            os.remove(self.cover_archivo)
        except OSError:
            pass

    def __unicode__(self):
        return self.nombre

    def __str__(self):
        return self.nombre

    def crear_cover(self, directorio):
        self.cover_archivo = directorio + 'cover.jpg'
        with open(self.cover_archivo, 'wb') as handle:
            request = requests.get(self.cover, stream=True)
            for block in request.iter_content():
                if not block:
                    break
                handle.write(block)
                
                
class Huron:

    def __init__(self, api_key, mix_url):
        r = requests.get(mix_url + '.json',
                         headers={'X-Api-Key': api_key,
                         'X-Api-Version': API_VERSION}).json()
        self.api_key = api_key
        self.mix = Mix(r['mix']['name'], r['mix']['id'], r['mix']['tracks_count'],
                       r['mix']['cover_urls']['sq500'])
        self.directorio = 'Descargas/' + r['mix']['name'] + '/'
        self.token = requests.get('http://8tracks.com/sets/new.json',
                                  headers={'X-Api-Key': api_key,
                                  'X-Api-Version': API_VERSION}).json()['play_token']

    def agregar_etiquetas(self, cancion):
        try:
            etiquetas = mutagen.id3.ID3(cancion.archivo)
        except mutagen.id3.ID3NoHeaderError:
            etiquetas = mutagen.id3.ID3()
        finally:
            etiquetas['TIT2'] = mutagen.id3.TIT2(encoding=3,
                    text=cancion.nombre)
            etiquetas['TALB'] = mutagen.id3.TALB(encoding=3,
                    text=cancion.album)
            etiquetas['TPE2'] = mutagen.id3.TPE2(encoding=3,
                    text=cancion.artista)
            etiquetas['TDRC'] = mutagen.id3.TDRC(encoding=3,
                    text=str(cancion.fecha))
            etiquetas.save(cancion.archivo)

    def agregar_cover(self, cancion):
        audio = MP3(cancion.archivo, ID3=mutagen.id3.ID3)
        audio.tags.add(mutagen.id3.APIC(encoding=3, mime='image/jpeg',
                       type=3, desc=u'Cover',
                       data=open(self.mix.cover_archivo, 'rb').read()))

        audio.save()

    def guardar(self, cancion):
        with open(cancion.archivo, 'wb') as handle:
            request = requests.get(cancion.url, stream=True)
            for block in request.iter_content(1024):
                if not block:
                    break
                handle.write(block)
        self.agregar_etiquetas(cancion)
        self.agregar_cover(cancion)

    def ejecutar(self):
        if not os.path.exists(self.directorio):
            os.makedirs(self.directorio)
        self.mix.crear_cover(self.directorio)

        for i in range(self.mix.canciones):
            inicio = time.clock()
            r = \
                requests.get('http://8tracks.com/sets/%s/next.json?mix_id=%s'
                              % (self.token, self.mix.id),
                             headers={'X-Api-Key': API_KEY,
                             'X-Api-Version': API_VERSION}).json()

            cancion = Cancion(
                r['set']['track']['id'],
                r['set']['track']['name'],
                self.mix.nombre,
                r['set']['track']['year'],
                r['set']['track']['performer'],
                r['set']['track']['track_file_stream_url'],
                self.directorio + self.clean_nombre(r['set']['track']['name']) + '.mp3',
                )

            self.debug(cancion, i)
            self.guardar(cancion)

            if i > 2:
                audio = MP3(cancion.archivo)
                time.sleep(int(audio.info.length) - int(time.clock()
                           - inicio))

            requests.get('http://8tracks.com/sets/%s/report.json?track_id=[%s]&mix_id=[%s]'
                          % (self.token, cancion.id, self.mix.id),
                         headers={'X-Api-Key': API_KEY,
                         'X-Api-Version': API_VERSION})

    def debug(self, cancion, i):
        print '%d%% - Descargando canción (%d de %d): %s' % (int((i * 100) / 32), i + 1, self.mix.canciones, str(cancion))
        
    def clean_nombre(self, nombre):
        return ''.join([c for c in nombre if c.isalpha()
                               or c.isdigit() or c == ' ' or c == '('
                               or c == ')' or c == '-']).rstrip()


if __name__ == '__main__':
    huron = Huron(API_KEY, (sys.argv[1] if len(sys.argv)
                  > 1 else raw_input('Ingresa URL del playlist\n')))
    huron.ejecutar()
