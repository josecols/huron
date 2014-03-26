#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import os
import sys
import string
import time
import re
import mutagen.id3
from mutagen import File
from mutagen.mp3 import MP3

API_KEY = 'ba584160f1b8564f82d78529eada82179edc0fbb'
API_VERSION = 3

class Discogs:
    
    def __init__(self):
        self.key = 'weYwLTpHLKfUBfWuYfdo'
        self.secret = 'itBsbZgbDZyiAIVWbhVaDYzFLfWKmINd'
        
         
class Soundcloud:
    
    def __init__(self, cliente, cancion):
        self.id = cliente
        self.cancion = cancion
        
    @staticmethod
    def atributos(url):
        return (url.partition('client_id=')[2], re.search(r'\d+', url).group())


class Cancion:
    
    v = "-_.() %s%s" % (string.ascii_letters, string.digits)

    def __init__(self, cancion, nombre, album, fecha, artista, url, archivo):
        self.id = str(cancion)
        self.nombre = ''.join(c for c in nombre if c in Cancion.v)
        self.album = album
        self.fecha = fecha
        self.artista = artista
        self.url = url
        self.archivo = archivo
        self.cover = {'url': None, 'archivo': archivo}
        self.sc = Soundcloud(*Soundcloud.atributos(url)) if 'soundcloud' in url else None
        
    def __del__(self):
        try:
            os.remove(self.cover['archivo'])
        except OSError:
            pass

    def __unicode__(self):
        return unicode(self.nombre + ' - ' + self.artista) 

    def __str__(self):
        return self.nombre + ' - ' + self.artista 
    
    def etiquetas(self):
        try:
            etiquetas = mutagen.id3.ID3(self.archivo)
        except mutagen.id3.ID3NoHeaderError:
            etiquetas = mutagen.id3.ID3()
        finally:
            try:
                etiquetas['TIT2']
            except KeyError:
                etiquetas['TIT2'] = mutagen.id3.TIT2(encoding=3, text=self.nombre)
            try:
                etiquetas['TALB']
            except KeyError:
                etiquetas['TALB'] = mutagen.id3.TALB(encoding=3, text=self.album)
            try:
                etiquetas['TPE2']
            except KeyError:
                etiquetas['TPE2'] = mutagen.id3.TPE2(encoding=3, text=self.artista)
            try:
                etiquetas['TDRC']
            except KeyError:
                etiquetas['TDRC'] = mutagen.id3.TDRC(encoding=3, text=str(self.fecha))        
            etiquetas.save(self.archivo)
            self.albumart()
            
    def albumart(self):
        if self.cover['archivo'].endswith('jpg'):                
            audio = File(self.archivo)        
            try:
                audio.tags['APIC:']
            except KeyError:                   
                data = open(self.cover['archivo'], 'rb').read()            
                audio.tags.add(mutagen.id3.APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=data))
                audio.save()
            
    def guardar_cover(self):
        self.cover['archivo'] = os.path.join(self.cover['archivo'], self.id + '.jpg')
        with open(self.cover['archivo'], 'wb') as handle:
            request = requests.get(self.cover['url'], stream=True)
            for block in request.iter_content():
                if not block:
                    break
                handle.write(block)
            handle.close()
    
    def guardar(self):
        if self.sc:
            soundcloud = requests.get('http://api.soundcloud.com/tracks/%s.json?client_id=%s' % (self.sc.cancion, self.sc.id)).json()
            if soundcloud['downloadable']:
                r = requests.get(self.url.replace('stream', 'download'), stream=True)
                self.archivo += re.search(r'\"(.+?)\"', r.headers.get('content-disposition')).group(0)[1:-1]
            else:
                r = requests.get(self.url, stream=True)
                self.archivo += self.nombre + '.' + soundcloud['original_format']
                if soundcloud['artwork_url']:
                    self.cover['url'] = soundcloud['artwork_url'].replace('large', 't300x300')
                    self.guardar_cover()
        else:
            r = requests.get(self.url, stream=True)
            self.archivo += self.nombre + '.m4a'
        
        with open(self.archivo, 'wb') as handle:
            for block in r.iter_content(1024):
                if not block:
                    break
                handle.write(block)
            handle.close()   
        self.etiquetas()    
        
    @staticmethod
    def atributos(r, archivo):
        return (r['set']['track']['id'], r['set']['track']['name'], r['set']['track']['release_name'],
                r['set']['track']['year'], r['set']['track']['performer'], r['set']['track']['track_file_stream_url'], archivo)


class Mix:

    def __init__(self, nombre, mix_id, canciones, cover, directorio):
        self.nombre = ''.join(c for c in nombre if c in Cancion.v)
        self.id = mix_id
        self.canciones = canciones
        self.cover = cover
        self.cover_archivo = None
        self.directorio = directorio        

    def __del__(self):
        try:
            os.remove(self.cover_archivo)
        except OSError:
            pass

    def __unicode__(self):
        return unicode(self.nombre)

    def __str__(self):
        return self.nombre    

    def guardar_cover(self, directorio):
        self.cover_archivo = directorio + 'cover.jpg'
        with open(self.cover_archivo, 'wb') as handle:
            request = requests.get(self.cover, stream=True)
            for block in request.iter_content():
                if not block:
                    break
                handle.write(block)
            handle.close()
                
    def guardar(self):
        if not os.path.exists(self.directorio):
            os.makedirs(self.directorio)
        
        print 'Descargando playlist %s.' % self.nombre    
        for i in range(self.canciones):            
            inicio = time.clock()            
            cancion = Cancion(*Cancion.atributos(Huron.siguiente(self.id), self.directorio))
            print '\tDescargando canción (%d de %d): %s' % (i + 1, self.canciones, cancion)                          
            cancion.guardar()                                  
            if i > 2:
                audio = MP3(cancion.archivo)
                time.sleep(int(audio.info.length) - int(time.clock() - inicio))
                
            Huron.reportar(cancion.id, self.id) 
            
    @staticmethod
    def atributos(r):
        return (r['mix']['name'], r['mix']['id'], r['mix']['tracks_count'],
                r['mix']['cover_urls']['sq500'], 'Descargas/' + r['mix']['name'] + '/')


class Huron:
    
    headers = {'X-Api-Key': API_KEY, 'X-Api-Version': API_VERSION}
    urls = {'token':'http://8tracks.com/sets/new.json',
            'next':'http://8tracks.com/sets/%s/next.json?mix_id=%s',
            'report':'http://8tracks.com/sets/%s/report.json?track_id=[%s]&mix_id=[%s]'}
    token = requests.get(urls['token'], headers=headers).json()['play_token']

    def __init__(self, mix_url):                
        self.mix = Mix(*Mix.atributos(requests.get(mix_url + '.json', headers=Huron.headers).json()))

    def ejecutar(self):
        self.mix.guardar()
        print "\n Listo."
        
    @staticmethod
    def siguiente(mix_id):
        return requests.get(Huron.urls['next'] % (Huron.token, mix_id), headers=Huron.headers).json()
    
    @staticmethod
    def reportar(cancion_id, mix_id):
        requests.get(Huron.urls['report'] % (Huron.token, cancion_id, mix_id), headers=Huron.headers)    


if __name__ == '__main__':
#     huron = Huron((sys.argv[1] if len(sys.argv) > 1 else raw_input('Ingresa URL del playlist\n')))
#     huron = Huron('http://8tracks.com/josecols/don-t-close-your-eyes')
    huron = Huron('http://8tracks.com/rpk213/majestic-casual')    
    huron.ejecutar()
