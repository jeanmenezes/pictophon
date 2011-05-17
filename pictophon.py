#!/usr/bin/env python
# coding=iso-8859-15

import sys
import subprocess
import shlex
from PIL import Image
import re
import os
import shutil
import csv
import audiotools
import glob
import messages

# checagem de rotina para argumentos {{{1

if len(sys.argv) != 2:
    print '''
    Bad usage: only one argument must be used,
    and it should be an image file name.
    
    Usage: ./pictophon.py <image_file>
    
    typing  ./pictophon.py
    or      ./pictophon.py help
    displays this help.
    '''
    sys.exit()
elif sys.argv[1] == 'help':
    print messages.welcome
    print '''
    Usage: ./pictophon.py <image_file>

    typing  ./pictophon.py
    or      ./pictophon.py help
    displays this help.

    '''
    print messages.helptext
    sys.exit()

# checar se o arquivo declarado é realmente uma imagem; {{{1
# em caso afirmativo, carrega o arquivo.

try:
    Image.open(sys.argv[1])
except IOError as detail:
    print sys.argv[1], "is not a valid image file!"
    sys.exit()
except:
    print "unexpected error:", sys.exc_info()[0]
    raise
    sys.exit()
else:
    pic = sys.argv[1]
    print messages.welcome

# declaração das variáveis principais {{{1

partes = pic.rsplit('.', 1)
base = partes[0]
extensao = partes[1]
destino = './' + base + '_pictophon'
chuckfile = './' + base + '.ck'
csvXYZ = './' + base + '.XYZ.csv'
csvxyz = './' + base + '.xyz.csv'


# declaração das funções {{{1


# gera_xyz {{{2
def gera_xyz(imagem):
    '''
    * reduz a imagem a 25% da dimensão em pixels e converte para GIF 64 cores;
    * gera um arquivo CSV com os dados de cores de canais XYZ para a imagem.
    '''

    print messages.crexyz

    comando = []
    comando.append('convert ./{0} -resize 25% ./tmp.{1}'.format(imagem, extensao))
    comando.append('convert ./tmp.{0} -dither FloydSteinberg -colors 64 ./{1}.small.gif'.format(extensao, base))
    comando.append('rm ./tmp.{0}'.format(extensao))
    comando.append('convert ./{0}.small.gif -colorspace XYZ ./tmp.txt'.format(base))

    comandos = [shlex.split(x) for x in comando]

    for i in comandos:
        subprocess.call(i)

    # aqui criamos o CSV propriamente dito, mais os auxiliares internos rgblist.tmp e occ_list.tmp {{{3

    with open('tmp.txt') as f:
        l = [line.split() for line in f]
        pen_col = [x[-2] for x in l[1:]]
        ult_col = [x[-1] for x in l[1:]]
        pen = list(set(pen_col))
        ult = list(set(ult_col))

        regex_xyz = re.compile('[xyz\(\)]')
        regex_hash = re.compile('\#')

    with open(csvXYZ, 'w') as fx:
        for j in ult:
            fx.write(regex_xyz.sub('', j) + '\n')

    with open('rgblist.tmp', 'w') as rl:
        for j in pen:
            rl.write(regex_hash.sub('', j) + '\n')

    with open('occ_list.tmp', 'w') as ol:
        occ = [pen_col.count(j) for j in pen]
        for k in sorted(occ, reverse=True):
            ol.write(str(k) + '\n')

    os.remove('./tmp.txt')


# calcula_xyz() {{{2
def calcula_xyz(csvfile):
    '''
    converte valores XYZ para xyz e gera um arquivo CSV para cálculos posteriores
    '''
    csv.register_dialect('xyzcsv', delimiter=',', quoting=csv.QUOTE_NONE)
    with open(csvfile, 'r') as f:
        csvf = csv.reader(f, 'xyzcsv')
        vals = []
        vals_xyz = []

        for line in csvf:
            v = [float(x) for x in line]
            vals.append(v)

        for i in vals:
            vl = ['{0:5f}'.format(x / sum(i)) for x in i]
            vals_xyz.append(vl)

    with open(csvxyz, 'w') as fx:
        csvfx = csv.writer(fx, 'xyzcsv')
        for line in vals_xyz:
            csvfx.writerow(line)


# mean() {{{2
def mean(col, csvfile):
    '''
    calcula a média dos valores XYZ (primeira etapa)
    '''

    with open(csvfile, 'r') as f:
        csvf = csv.reader(f, 'xyzcsv')
        vals_mean = []
        for line in csvf:
            v = line[col]
            vals_mean.append(int(v))

        return vals_mean


# media() {{{2
def media(r, csvfile):
    '''
    segunda etapa para mean()
    '''

    print messages.crechuck

    vals_tot = []
    for i in range(r):
        vm = mean(i, csvfile)
        vmp = sum(vm) / len(vm)
        vals_tot.append(vmp)

    med_tot = sum(vals_tot) / len(vals_tot)
    return med_tot


# cria_chuck() {{{3
def cria_chuck():
    '''
    cria arquivo .ck para geração de sons via ChucK
    '''
    mt = media(3, csvXYZ)

    with open(chuckfile, 'w') as ck:
        with open('./.chuck_class', 'r') as cc:
            for line in cc:
                ck.write(line)
        ck.write('Pixel pix;\n')

        with open(csvXYZ, 'r') as fc:
            csvf = csv.reader(fc, 'xyzcsv')
            fx, fy, fz = [], [], []
            for line in csvf:
                fx.append(line[0])
                fy.append(line[1])
                fz.append(line[2])

        with open(csvxyz, 'r') as fcx:
            csvfx = csv.reader(fcx, 'xyzcsv')
            ax, ay, az = [], [], []
            for line in csvfx:
                ax.append(line[0])
                ay.append(line[1])
                az.append(line[2])

        regex_nl = re.compile("\n")

        with open('./occ_list.tmp', 'r') as ol:
            durs = [regex_nl.sub('', line) + '::ms' for line in ol]

        with open('./rgblist.tmp', 'r') as rl:
            fnames = [regex_nl.sub('', line) + '.aiff' for line in rl]

        for a, b, c, d, e, f, g, h in map(None, fx, fy, fz, ax, ay, az, durs, fnames):
            ck.write("pix.set_vars({0:5f}, {1}, {2}, {3}, {4}, {5}, {6}, {7});\n".format(mt, g, a, b, c, d, e, f))
            ck.write('pix.todisk("{0}");\n'.format(h))


# cria_aif() {{{2
def cria_aif(ckfile):
    '''
    cria arquivos .aif usando chuck
    '''

    print messages.creaiff

    command = shlex.split("chuck --srate44100 --silent {0}".format(ckfile))
    subprocess.call(command)
    os.mkdir(destino)
    os.mkdir(destino + "/.mp3")


# conv_mp3() {{{2
def conv_mp3():
    '''
    * cria arquivos .mp3 comprimidos para a página html de referência;
    * move os arquivos .aif e .wav para a pasta de destino
    '''

    print messages.crehtml

    wf = glob.glob('./*.aiff')
    regex_wav = re.compile('aiff')
    for i in wf:
        audiotools.MP3Audio.from_pcm(regex_wav.sub('mp3', i), audiotools.open(i).to_pcm())
        shutil.move(i, destino)
        shutil.move(regex_wav.sub('mp3', i), destino + '/.mp3/')


# cria_ref_html() {{{2
def cria_ref_html():
    with open('color_ref.html', 'w') as html:
        html.write('''
        <html>
        <head>
        <title>RGB color reference for project {0}</title>\n\
        </head>

        <body>

        <h1>RGB color reference for project <i>{1}</i></h1>\n\

        <table>
        '''.format(base, base))
        aiffs = glob.glob(destino + '/*.aiff')
        regex_dash = re.compile('.*\/')
        regex_wav = re.compile('.aiff')
        regex_nl = re.compile('\n')

        with open('./occ_list.tmp', 'r') as ol:
            occs = [regex_nl.sub('', line) for line in ol]
        with open('./rgblist.tmp', 'r') as rl:
            rgbs = [regex_nl.sub('', line) for line in rl]

        for i in aiffs:
            rgb = regex_dash.sub('#', regex_wav.sub('', i))
            nrgb = regex_dash.sub('', regex_wav.sub('', i))
            j = occs[rgbs.index(nrgb)]
            html.write('<tr>\n')
            html.write('<td bgcolor={0}>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>\n'.format(rgb))
            html.write('<td>{0}.wav</td>\n'.format(nrgb))
            html.write('<td>{0} occurrences</td>\n'.format(j))
            html.write('<td><audio src="./.mp3/{0}.mp3" controls="controls" type="audio/mp3"></td>\n'.format(nrgb))
            html.write('</tr>\n\n')

        html.write('''
        </table>

        </body>
        </html>
        ''')

    shutil.move('./color_ref.html', destino)


# cleanup() {{{2
def cleanup():
    '''
    limpa arquivos temporários
    '''

    print messages.cleanup

    os.remove(base + ".small.gif")
    os.remove('./rgblist.tmp')
    os.remove('./occ_list.tmp')
    shutil.move(chuckfile, destino)
    shutil.move(csvXYZ, destino)
    shutil.move(csvxyz, destino)


# chamando as funções para execução do programa {{{1

gera_xyz(pic)
calcula_xyz(csvXYZ)
cria_chuck()
cria_aif(chuckfile)
conv_mp3()
cria_ref_html()
cleanup()

print '\nOkay! You can find your .aiff and various reference files at {0}.\n'.format(destino)
