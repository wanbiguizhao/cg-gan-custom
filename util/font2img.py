# -*- coding: utf-8 -*-

import os
import shutil
import sys

import argparse
import numpy as np

from PIL import Image, ImageFont, ImageDraw
import json
import collections
import re
from fontTools.ttLib import TTFont
#from fontTools.ttx import TTFont
from tqdm import tqdm
import random
from glob import glob

#from torch import nn
#from torchvision import transforms
PROJECT_DIR=os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(PROJECT_DIR)
try:
    from charset_util import processGlyphNames
except:
    from .charset_util import processGlyphNames

def is_contains_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False
def font2img(base_src_font_dir,base_dst_img_dir):
    def _font2img(src_font_dir,dst_img_dir):
        font=TTFont(src_font_dir,fontNumber=0)
        charset = processGlyphNames(font.getGlyphNames())
        print(src_font_dir,len(charset))
        img_font=ImageFont.truetype(src_font_dir,64)
        cnt=0
        for index, ch in enumerate(charset):
            if not is_contains_chinese(ch):
                continue
            cnt+=1
            img = Image.new("L", (canvas_size*2 , canvas_size*2 ), 0)
            draw = ImageDraw.Draw(img)
            draw.text((0, 0), ch, 255, font=img_font)
            bbox = img.getbbox()
            l, u, r, d = bbox
            l = max(0, l - 5)
            u = max(0, u - 5)
            r = min(canvas_size * 2 - 1, r + 5)
            d = min(canvas_size * 2 - 1, d + 5)
            text_region_img=img.crop((l,u,r,d))
            text_high, text_wide = text_region_img.size
            new_len_side=max(text_high,text_wide)
            square_img=Image.new("L",(new_len_side,new_len_side),0)
            square_img.paste(text_region_img,( (new_len_side-text_high)//2, (new_len_side-text_wide)//2))
            square_img = square_img.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)

            np_square_img=255-np.array(square_img)
            square_img=Image.fromarray(np_square_img)
            square_img.save(f"{dst_img_dir}/{str(cnt).rjust(4,'0')}_{ch}.png")
            if cnt>4000:
                break
    
    canvas_size=64
    assert base_src_font_dir is not None
    assert os.path.exists(base_src_font_dir)
    font_instance_dict={}
    shutil.rmtree(base_dst_img_dir)
    for index,font_file in enumerate(os.listdir(base_src_font_dir)):
        if not os.path.exists(f"{base_dst_img_dir}/{index}"):
            os.makedirs(f"{base_dst_img_dir}/{index}")
        print(index,font_file)
        _font2img(f"{base_src_font_dir}/{font_file}",f"{base_dst_img_dir}/{index}")
    png_path_list=[]
    for png_path in glob(f"{base_dst_img_dir}/*/*.png"):
        png_path_list.append(png_path[len(base_dst_img_dir)+1:])
    
    open(f"{base_dst_img_dir}/images_info_list","w").write("\n".join(sorted(png_path_list,key=lambda x: x[-5:])))
    # 生成所有字体文件图片信息


    

        # l, u, r, d = bbox
        # l = max(0, l - 5)
        # u = max(0, u - 5)
        # r = min(canvas_size  - 1, r + 5)
        # d = min(canvas_size  - 1, d + 5)
        # print(l, u, r, d)
        # text_region_img=img.crop((l,u,r,d))
        # text_high, text_wide = text_region_img.size
        # new_len_side=max(text_high,text_wide)


def word2img(base_src_font_dir,base_dst_img_dir):
    def drawfont2img(src_font_dir,dst_img_dir,char_index_dict):
        local_charset=get_font_charset(src_font_dir)
        img_font=ImageFont.truetype(src_font_dir,canvas_size)
        for  ch in tqdm(local_charset):
            label_w, label_h = img_font.getsize(ch)
            img_target =Image.new('RGB', (label_w,label_h),(255,255,255))
            drawBrush = ImageDraw.Draw(img_target)
            drawBrush.text((0,0),ch,fill=(0,0,0),font = img_font)
            img_target.save(f"{dst_img_dir}/{str(char_index_dict[ch]).rjust(5,'0')}_{ch}.png")
    canvas_size=64
    assert base_src_font_dir is not None
    assert os.path.exists(base_src_font_dir)
    shutil.rmtree(base_dst_img_dir)
    merge_charset=set()
    for index,font_file in enumerate(os.listdir(base_src_font_dir)):
        if not os.path.exists(f"{base_dst_img_dir}/{index}"):
            os.makedirs(f"{base_dst_img_dir}/{index}")
        src_font_dir=f"{base_src_font_dir}/{font_file}"
        font_charset=get_font_charset(src_font_dir)
        merge_charset.update(font_charset)        
        print(index,src_font_dir,len(font_charset),len(merge_charset))
    Char_Index_Dict={char:index for index,char in enumerate(sorted(list(merge_charset)))}
    print(len(Char_Index_Dict))
    for index,font_file in enumerate(os.listdir(base_src_font_dir)):
        src_font_dir=f"{base_src_font_dir}/{font_file}"
        drawfont2img(src_font_dir,f"{base_dst_img_dir}/{index}",Char_Index_Dict)

    png_path_list=[]
    for png_path in glob(f"{base_dst_img_dir}/*/*.png"):
        png_path_list.append(png_path[len(base_dst_img_dir)+1:])
    open(f"{base_dst_img_dir}/images_info_list","w").write("\n".join(sorted(png_path_list,key=lambda x: x[-5:])))



def get_font_charset(font_dir):
    font=TTFont(font_dir,fontNumber=0)
    unicode_list=font.getBestCmap().keys()
    #local_charset = processGlyphNames(font.getGlyphNames())
    font_charset=[chr(ch) for ch in unicode_list if is_contains_chinese(chr(ch))]
    return font_charset
def sentence2img(base_src_font_dir,base_dst_img_dir):
    def drawfonts2img(image_font_List,dst_img_dir,intersection_charset):
        for index, ch in tqdm(enumerate(local_charset)):
            final_img=Image.new("L", (canvas_size*len(image_font_List) , canvas_size ), 255)

            for font_index,img_font in enumerate(image_font_List):
                img=Image.new("L", (canvas_size*2 , canvas_size*2 ), 0)
                draw = ImageDraw.Draw(img)
                draw.text((0, 0), ch, 255, font=img_font)
                draw = ImageDraw.Draw(img)
                bbox = img.getbbox()
                if not bbox:
                    continue
                l, u, r, d = bbox
                l = max(0, l - 5)
                u = max(0, u - 5)
                r = min(canvas_size * 2 - 1, r + 5)
                d = min(canvas_size * 2 - 1, d + 5)
                text_region_img=img.crop((l,u,r,d))

                text_high, text_wide = text_region_img.size
                new_len_side=max(text_high, text_wide)
                square_img=Image.new("L",(new_len_side,new_len_side),0)
                square_img.paste(text_region_img,( (new_len_side-text_high)//2, (new_len_side-text_wide)//2))
                square_img = square_img.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)
                np_square_img=255-np.array(square_img)
                square_img=Image.fromarray(np_square_img)
                final_img.paste(square_img,(font_index*canvas_size,0))
            final_img.save(f"{dst_img_dir}/{str(index).rjust(4,'0')}_{ch}.png")
    canvas_size=64
    assert base_src_font_dir is not None
    assert os.path.exists(base_src_font_dir)
    #shutil.rmtree(base_dst_img_dir,ignore_errors=True)
    merge_charset=set()
    intersection_charset=set()
    image_font_List=[]
    for index,font_file in enumerate(os.listdir(base_src_font_dir)):
        src_font_dir=f"{base_src_font_dir}/{font_file}"
        image_font_List.append(ImageFont.truetype(src_font_dir,canvas_size))
        local_charset=get_font_charset(src_font_dir)
        merge_charset.update(local_charset)
        if len(intersection_charset)==0:
            intersection_charset.update(local_charset)
        else:
            intersection_charset=intersection_charset.intersection(local_charset)
        print(index,src_font_dir,len(local_charset),len(merge_charset),len(intersection_charset))
    dst_image_dir=f"{base_dst_img_dir}/x"
    os.makedirs(dst_image_dir,exist_ok=True)
    drawfonts2img(image_font_List,dst_image_dir,intersection_charset)
def default_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-font', type=str,dest="src_font", default=None, help='path of the source font')
    parser.add_argument('--dst-img-dir', type=str, dest="dst_img_dir",default=None, help='path of the target imgs')
    return parser 

if __name__ == "__main__":
    parser=default_args_parser()
    args = parser.parse_args()
    #font2img(base_src_font_dir=args.src_font,base_dst_img_dir=args.dst_img_dir)
    #font2img("/home/liukun/share/font/","tmp/images")
    word2img("/home/liukun/share/font2/","tmp/images")
    #sentence2img("/home/liukun/share/font2/","tmp/images")