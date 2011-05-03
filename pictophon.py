#!/usr/bin/env python
# coding=iso-8859-15

import sys
import subprocess
import shlex
from PIL import Image
import re
import os

# checagem de rotina para argumentos

if len(sys.argv) != 2:
    print "Bad usage: only one argument must be used, and it should be an image file name"
    sys.exit()

# checar se o arquivo declarado é realmente uma imagem;
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

# declaração das variáveis e funções principais

partes = pic.rsplit('.', 1)
base = partes[0]
extensao = partes[1]

def gera_xyz(imagem):
    '''
    * reduz a imagem a 25% da dimensão em pixels e converte para GIF 64 cores;
    * gera um arquivo CSV com os dados de cores de canais XYZ para a imagem.
    '''

    comando = []
    comando.append('convert ./{0} -resize 25% ./tmp.{1}'.format(imagem, extensao))
    comando.append('convert ./tmp.{0} -dither FloydSteinberg -colors 64 ./{1}.small.gif'.format(extensao, base))
    comando.append('rm ./tmp.{0}'.format(extensao))
    comando.append('convert ./{0}.small.gif -colorspace XYZ ./tmp.txt'.format(base))
    
    comandos = [ shlex.split(x) for x in comando ]

    for i in comandos:
        subprocess.call(i)

    # aqui criamos o CSV propriamente dito, mais os auxiliares internos .rgblist e .occ_list

    with open('tmp.txt') as f:
        l = [ line.split() for line in f ]
        pen_col = [ x[-2] for x in l[1:] ]
        ult_col = [ x[-1] for x in l[1:] ]
        pen = list(set(pen_col))
        ult = list(set(ult_col))

        regex_xyz = re.compile('[xyz\(\)]')

    with open(base+".XYZ.csv", 'w') as fx:
        for j in ult:
            fx.write(regex_xyz.sub('', j)+'\n')
    
    with open('.rgblist', 'w') as rl:
        for j in pen:
            rl.write(j+'\n')

    with open('.occ_list', 'w') as ol:
        occ = [ pen_col.count(j) for j in pen ]
        for k in sorted(occ, reverse=True):
            ol.write(str(k)+'\n')

    os.remove('./tmp.txt')

gera_xyz(pic)
