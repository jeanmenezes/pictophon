#!/usr/bin/env python
# coding=iso-8859-15

# importação de módulos {{{1

import sys
import subprocess
import shlex
from pgmagick import Image, Blob
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
    print messages.strings['welcome']
    print '''
    Usage: ./pictophon.py <image_file>

    typing  ./pictophon.py
    or      ./pictophon.py help
    displays this help.

    '''
    print messages.strings['helptext']
    sys.exit()


# checar se o arquivo declarado é realmente uma imagem; {{{1
# em caso afirmativo, carrega o arquivo.

def check_img():
    '''
    Checar se o arquivo declarado é realmente uma imagem;
    em caso afirmativo, carrega o arquivo
    '''

    try:
        check = Image()
        check.ping(sys.argv[1])
    except RuntimeError:
        print sys.argv[1], "is not a valid image file!"
        sys.exit()
    except:
        print "unexpected error:", sys.exc_info()[0]
        raise
        sys.exit()
    else:
        return sys.argv[1]


# declaração das variáveis principais {{{1

PIC = check_img()
PARTES = PIC.rsplit('.', 1)
BASE = PARTES[0]
DESTINO = './' + BASE + '_pictophon'
CHUCKFILE = './' + BASE + '.ck'
csvXYZ = './' + BASE + '.XYZ.csv'
csvxyz = './' + BASE + '.xyz.csv'
REGEX_XYZ = re.compile('[\(\)]')
REGEX_HASH = re.compile('\#')


# declaração das funções {{{1

# safe_cleanup {{{2

def safe_cleanup():
    '''
    Limpa arquivos temporários em caso de erro
    '''

    os.remove('./tmp.txt')
    os.remove(CHUCKFILE)
    os.remove(csvXYZ)
    os.remove(csvxyz)
    for file in glob.glob('./*.aiff'):
        os.remove(file)


# gera_xyz {{{2

def gera_xyz(imagem):
    '''
    * reduz a imagem a 25% da dimensão em pixels e converte para GIF 64 cores;
    * gera um arquivo .txt com os dados pixel a pixel, quanto às cores em RGB
      e xyz
    '''

    print messages.strings['welcome']
    print messages.strings['crexyz']

    img_base = Blob(open(imagem).read())
    img_alvo = Image(img_base)
    img_alvo.magick('GIF')
    img_alvo.colorSpace = 'XYZ'
    img_alvo.scale('25%')
    img_alvo.quantizeColors(64)
    img_alvo.quantizeDither(img_alvo.quantize(64))
    img_alvo.write('./tmp.txt')

    with open('./tmp.txt', 'r') as tt:
        return tt.readlines()


# limpeza_inicial {{{2

def limpeza_inicial(entrada):
    '''
    Limpa caracteres desnecessários para facilitar o trabalho de parse_csv()
    '''

    strips = re.compile('.*: ')
    pars = re.compile('[\(][ ]*')
    rexps = re.compile('[\,][ ]*')

    return [strips.sub('', pars.sub('(', rexps.sub(',', line))) for line in entrada]


# parse_csv {{{2

def parse_csv(txtfile):
    '''
    Gera listas brutas de RGB, XYZ e número de ocorrência de cada cor.
    '''

    limpo = limpeza_inicial(txtfile)

    l = [line.split() for line in limpo]
    pen_col = [x[-2] for x in l]
    ult_col = [x[-1] for x in l]
    return {'rgb': list(set(ult_col)),
            'XYZ': list(set(pen_col)),
            'ocorrencias': [ult_col.count(j) for j in list(set(ult_col))]}


# cria dicionário para uso persistente {{{2

DIC = parse_csv(gera_xyz(PIC))


# rgblist, occ_list {{{2

def rgblist(coluna):
    '''
    Estrutura a lista de dados RGB
    '''

    return [REGEX_HASH.sub('', j) + '\n' for j in coluna]

def occ_list(coluna):
    '''
    Estrutura a lista de ocorrências de cada cor
    '''

    return [str(k) + '\n' for k in sorted(coluna, reverse=True)]


# gera_csv {{{2

def gera_csv():
    '''
    Estrutura o arquivo .csv com os dados XYZ da imagem
    '''

    with open(csvXYZ, 'w') as fx:
        for j in DIC['XYZ']:
            fx.write(REGEX_XYZ.sub('', j) + '\n')


# calcula_xyz() {{{2

def calcula_xyz(csvfile):
    '''
    converte valores XYZ para xyz e gera um arquivo CSV para cálculos posteriores
    '''

    csv.register_dialect('xyzcsv', delimiter=',', quoting=csv.QUOTE_NONE)
    with open(csvfile, 'r') as f:
        csvf = csv.reader(f, 'xyzcsv')
        vals_xyz = []

        vals = [[float(x) for x in line] for line in csvf]

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

    print messages.strings['crechuck']

    vals_tot = []
    for i in range(r):
        vm = mean(i, csvfile)
        vmp = sum(vm) / len(vm)
        vals_tot.append(vmp)

    med_tot = sum(vals_tot) / len(vals_tot)
    return med_tot


# cria_chuck() {{{2

def cria_chuck():
    '''
    cria arquivo .ck para geração de sons via ChucK
    '''

    mt = media(3, csvXYZ)

    with open(CHUCKFILE, 'w') as ck:
        with open('./chuck_template', 'r') as cc:
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
        durs = [regex_nl.sub('', line) + '::ms' for line in occ_list(DIC['ocorrencias'])]
        fnames = [regex_nl.sub('', line) + '.aiff' for line in rgblist(DIC['rgb'])]

        for a, b, c, d, e, f, g, h in map(None, fx, fy, fz, ax, ay, az, durs, fnames):
            ck.write("pix.set_vars({0:5f}, {1}, {2}, {3}, {4}, {5}, {6}, {7});\n".format(mt, g, a, b, c, d, e, f))
            ck.write('pix.todisk("{0}");\n'.format(h))


# cria_aif() {{{2

def cria_aif(ckfile):
    '''
    cria arquivos .aif usando ChucK
    '''

    print messages.strings['creaiff']

    command = shlex.split("chuck --srate44100 --silent {0}".format(ckfile))
    subprocess.call(command)

    try:
        os.mkdir(DESTINO)
        os.mkdir(DESTINO + "/mp3")
    except OSError:
        print 'Directory {0} already exists. Remove or rename it before running this command again.'.format(DESTINO)
        safe_cleanup()
        sys.exit()
    except:
        print "unexpected error:", sys.exc_info()[0]
        raise
        safe_cleanup()
        sys.exit()


# conv_mp3() {{{2

def conv_mp3():
    '''
    * cria arquivos .mp3 comprimidos para a página html de referência;
    * move os arquivos .aif e .wav para a pasta de DESTINO
    '''

    print messages.strings['crehtml']

    wf = glob.glob('./*.aiff')
    regex_wav = re.compile('aiff')
    for i in wf:
        audiotools.MP3Audio.from_pcm(regex_wav.sub('mp3', i), audiotools.open(i).to_pcm())
        shutil.move(i, DESTINO)
        shutil.move(regex_wav.sub('mp3', i), DESTINO + '/mp3/')


# cria_ref_html() {{{2

def cria_ref_html(basename, dir_destino):
    '''
    Cria página html com referência para cada arquivo de som
    com sua respectiva cor e número de ocorrências
    '''

    with open('color_ref.html', 'w') as html:
        html.write('''
        <html>
        <head>
        <title>RGB color reference for project {0}</title>\n\
        </head>

        <body>

        <h1>RGB color reference for project <i>{1}</i></h1>\n\

        <table>
        '''.format(basename, basename))

        aiffs = glob.glob(dir_destino + '/*.aiff')
        regex_dash = re.compile('.*\/')
        regex_wav = re.compile('.aiff')
        regex_nl = re.compile('\n')

        occs = [regex_nl.sub('', line) for line in occ_list(DIC['ocorrencias'])]
        rgbs = [regex_nl.sub('', line) for line in rgblist(DIC['rgb'])]

        for i in aiffs:
            rgb = regex_dash.sub('#', regex_wav.sub('', i))
            nrgb = regex_dash.sub('', regex_wav.sub('', i))
            j = occs[rgbs.index(nrgb)]
            html.write('<tr>\n')
            html.write('<td bgcolor={0}>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>\n'.format(rgb))
            html.write('<td>{0}.wav</td>\n'.format(nrgb))
            html.write('<td>{0} occurrences</td>\n'.format(j))
            html.write('<td><audio src="./mp3/{0}.mp3" controls="controls" type="audio/mp3"></td>\n'.format(nrgb))
            html.write('</tr>\n\n')

        html.write('''
        </table>

        </body>
        </html>
        ''')

    shutil.move('./color_ref.html', DESTINO)


# cleanup() {{{2

def cleanup():
    '''
    limpa arquivos temporários
    '''

    print messages.strings['cleanup']

    os.remove('./tmp.txt')
    shutil.move(CHUCKFILE, DESTINO)
    shutil.move(csvXYZ, DESTINO)
    shutil.move(csvxyz, DESTINO)


# chamando as funções para execução do programa {{{1

def main():
    gera_csv()
    calcula_xyz(csvXYZ)
    cria_chuck()
    cria_aif(CHUCKFILE)
    conv_mp3()
    cria_ref_html(BASE, DESTINO)
    cleanup()
    print '\nOkay! You can find your .aiff and various reference files at {0}.\n'.format(DESTINO)


main()
