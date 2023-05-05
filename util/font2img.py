# -*- coding: utf-8 -*-

import os
import sys

import argparse
import numpy as np

from PIL import Image, ImageFont, ImageDraw
import json
import collections
import re
from fontTools.ttLib import TTFont
from tqdm import tqdm
import random

#from torch import nn
#from torchvision import transforms
PROJECT_DIR=os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(PROJECT_DIR)
from charset_util import processGlyphNames

src_fonts_path="data/font/方正楷体_GBK.ttf"
src_font = TTFont(src_fonts_path)
src_char_set = processGlyphNames(src_font.getGlyphNames())
print(len(src_char_set))


def font2img(src_font,dst_img_dir):
    canvas_size=64
    assert src_font is not None
    assert os.path.exists(src_font)
    if not os.path.isdir(dst_img_dir):
        os.makedirs(dst_img_dir)
    font = TTFont(src_font)
    charset = processGlyphNames(font.getGlyphNames())
    img_font=ImageFont.truetype(src_font,64)
    for ch in charset:
        
        img = Image.new("L", (canvas_size , canvas_size ), 0)
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), ch, 255, font=img_font)
        
        print("hehe",ch)
        bbox = img.getbbox()
        print(bbox)
        # l, u, r, d = bbox
        # l = max(0, l - 5)
        # u = max(0, u - 5)
        # r = min(canvas_size  - 1, r + 5)
        # d = min(canvas_size  - 1, d + 5)
        # print(l, u, r, d)
        # text_region_img=img.crop((l,u,r,d))
        # text_high, text_wide = text_region_img.size
        # new_len_side=max(text_high,text_wide)
        np_square_img=255-np.array(img)
        square_img=Image.fromarray(np_square_img)
        square_img.save(f"{dst_img_dir}/{ch}.png")
        break
    


def default_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-font', type=str,dest="src_font", default=None, help='path of the source font')
    parser.add_argument('--dst-img-dir', type=str, dest="dst_img_dir",default=None, help='path of the target imgs')
    return parser 

if __name__ == "__main__":
    parser=default_args_parser()
    args = parser.parse_args()
    font2img(src_font=args.src_font,dst_img_dir=args.dst_img_dir)