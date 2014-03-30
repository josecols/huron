#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import string
import subprocess
import requests
import mutagen.id3
from mutagen import File


class Discogs:
    
    urls = {'search': 'http://api.discogs.com/database/search?q=%s&artist=%s',
            'release':'http://api.discogs.com/releases/%s'}
    
    def __init__(self, cancion):
        self.key = 'weYwLTpHLKfUBfWuYfdo'
        self.secret = 'itBsbZgbDZyiAIVWbhVaDYzFLfWKmINd'
        self.cancion = cancion
        
    def buscar(self):
        r = requests.get(Discogs.urls['search'] % (self.cancion, self.cancion.artista)).json()
        return r
    
    def etiquetas(self):
        r = self.buscar()
        if len(r['results']) > 0:
            return (r['results'][0]['title'].split('-')[1].strip(),
                    r['results'][0]['year'].strip(),
                    ', '.join(g.strip() for g in r['results'][0]['genre']),
                    self.cover(r['results'][0]['id'])) 
        return (None, None, None, None)
    
    def cover(self, release):
        r = requests.get(Discogs.urls['release'] % release).json()
        try:
            return r['images'][0]['uri'].replace('api.discogs.com', 's.pixogs.com').strip()
        except KeyError:
            return None
         
         
class Soundcloud:
    
    urls = {'track': 'http://api.soundcloud.com/tracks/%s.json?client_id=%s'}
    
    def __init__(self, cliente, cancion):
        self.id = cliente
        self.cancion = cancion
                    
    @staticmethod
    def atributos(url):
        return (url.partition('client_id=')[2], re.search(r'\d+', url).group())
   
    
class EightTracks:

    headers = {'X-Api-Key': 'ba584160f1b8564f82d78529eada82179edc0fbb', 'X-Api-Version': 3}
    urls = {'token':'http://8tracks.com/sets/new.json',
            'next':'http://8tracks.com/sets/%s/next.json?mix_id=%s',
            'report':'http://8tracks.com/sets/%s/report.json?track_id=[%s]&mix_id=[%s]'}
    token = requests.get(urls['token'], headers=headers).json()['play_token']

    def __init__(self, mix_url):                
        self.mix = Mix(*Mix.atributos(requests.get(mix_url + '.json', headers=EightTracks.headers).json()))
        os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(os.getcwd(), 'cacert.pem')

    def guardar(self):
        self.mix.guardar()
        print "\n Listo."
        
    @staticmethod
    def siguiente(mix_id):
        return requests.get(EightTracks.urls['next'] % (EightTracks.token, mix_id), headers=EightTracks.headers).json()
    
    @staticmethod
    def reportar(cancion_id, mix_id):
        requests.get(EightTracks.urls['report'] % (EightTracks.token, cancion_id, mix_id), headers=EightTracks.headers)    


class Cancion:
    
    v = "-_.() %s%s" % (string.ascii_letters, string.digits)

    def __init__(self, cancion, nombre, album, fecha, artista, url, archivo, mix_cover):
        self.id = str(cancion)
        self.nombre = ''.join(c for c in nombre if c in Cancion.v)
        self.album = None if album.isdigit() or 'Uploaded by' in album else album
        self.fecha = fecha
        self.artista = artista
        self.genero = None
        self.url = url
        self.archivo = archivo
        self.cover = {'url': None, 'archivo': archivo, 'mix': mix_cover}
        self.sc = Soundcloud(*Soundcloud.atributos(url)) if 'soundcloud' in url else None
        self.discogs = None
        
    def __del__(self):
        try:
            os.remove(self.cover['archivo'])
        except OSError:
            pass
        
    def __exit__(self, *err):
        self.eliminar()

    def __unicode__(self):
        return unicode(self.nombre + ' - ' + self.artista) 

    def __str__(self):
        return self.nombre + ' - ' + self.artista 
    
    def actualizar(self):
        self.discogs = Discogs(self)
        (album, fecha, genero, cover) = self.discogs.etiquetas()
        
        if self.album is None:
            self.album = self.artista if album is None else album
        if self.fecha is None:
            self.fecha = '' if fecha is None else fecha
        if self.genero is None:
            self.genero = '' if genero is None else genero        
        if self.cover['url'] is None:
            self.cover['url'] = self.cover['mix'] if cover is None else cover
            self.guardar_cover()
    
    def eliminar(self):
        try:
            os.remove(self.cover['archivo'])
        except OSError:
            pass
    
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
            try:
                etiquetas['TCON']
            except KeyError:
                etiquetas['TCON'] = mutagen.id3.TCON(encoding=3, text=self.genero)                
            etiquetas.save(self.archivo)
            
            if self.cover['archivo'].endswith('jpg'):                
                audio = File(self.archivo)        
                try:
                    audio.tags['APIC:']
                except KeyError:                   
                    data = open(self.cover['archivo'], 'rb').read()            
                    audio.tags.add(mutagen.id3.APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=data))
                    audio.save()
                    
    def guardar(self):
        if self.sc:
            soundcloud = requests.get(Soundcloud.urls['track'] % (self.sc.cancion, self.sc.id)).json()
            if soundcloud['downloadable']:
                r = requests.get(self.url.replace('stream', 'download'), stream=True)
                self.archivo += re.search(r'\"(.+?)\"', r.headers.get('content-disposition')).group(0)[1:-1]
                self.cover['url'] = ''
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
            
        if not self.archivo.endswith('mp3'):
            try:
                subprocess.call(['ffmpeg', '-i', os.path.abspath(self.archivo), os.path.abspath(self.archivo[:-3] + 'mp3')],
                                stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))            
                os.remove(self.archivo)
                self.archivo = self.archivo[:-3] + 'mp3'
            except OSError:
                print '\nNo se pudo encontrar ffmpeg. Algunas canciones no serán convertidas a MP3.\n'
                return
        self.actualizar()
        self.etiquetas()           
            
    def guardar_cover(self):
        headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; WindowsNT)',
                   'Accept' :'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
                   'Accept-Language' : 'fr-fr,en-us;q=0.7,en;q=0.3',
                   'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        }
        r = requests.get(self.cover['url'], headers=headers, stream=True)
        self.cover['archivo'] = os.path.join(self.cover['archivo'], self.id + '.jpg')
        with open(self.cover['archivo'], 'wb') as handle:            
            for block in r.iter_content():
                if not block:
                    break
                handle.write(block)
            handle.close() 
        
    @staticmethod
    def atributos(r, archivo, mix_cover):
        return (r['set']['track']['id'], r['set']['track']['name'], r['set']['track']['release_name'],
                r['set']['track']['year'], r['set']['track']['performer'], r['set']['track']['track_file_stream_url'],
                archivo, mix_cover)


class Mix:

    def __init__(self, nombre, mix_id, canciones, cover, directorio):
        self.nombre = ''.join(c for c in nombre if c in Cancion.v)
        self.id = mix_id
        self.canciones = canciones
        self.cover = {'url': cover, 'archivo': None}
        self.directorio = directorio        

    def __unicode__(self):
        return unicode(self.nombre)

    def __str__(self):
        return self.nombre    
                
    def guardar(self):
        if not os.path.exists(self.directorio):
            os.makedirs(self.directorio)
        
        print u'Descargando playlist %s.' % self.nombre    
        for i in range(self.canciones):            
            inicio = time.clock()            
            cancion = Cancion(*Cancion.atributos(EightTracks.siguiente(self.id), self.directorio, self.cover['url']))
            print u'\tDescargando canción (%d de %d): %s' % (i + 1, self.canciones, cancion)                       
            cancion.guardar()                                  
            if i > 2 and i < self.canciones:
                audio = File(cancion.archivo)
                time.sleep(int(audio.info.length) - int(time.clock() - inicio))
            
            EightTracks.reportar(cancion.id, self.id)
            cancion.eliminar()    
            
    @staticmethod
    def atributos(r):
        return (r['mix']['name'], r['mix']['id'], r['mix']['tracks_count'],
                r['mix']['cover_urls']['sq500'], 'Descargas/' + r['mix']['name'] + '/')


if __name__ == '__main__':
    huron = EightTracks((sys.argv[1] if len(sys.argv) > 1 else raw_input('Ingresa URL del playlist\n')))    
    huron.guardar()
