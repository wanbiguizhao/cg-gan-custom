
import torch
import os
import shutil
from options.infer_options import InferOptions
import data.lmdb_dataset as lmdb_dataset
from models import create_model
from util import util
#from util.visualizer import save_single_image
from util.font2img import is_contains_chinese
from PIL import Image,ImageDraw,ImageFont
from data.infer_dataset import  InferDataset,HackInferDataset,HackFontInferDataset
from tqdm import tqdm
def draw(font_path,label,save_dir):
    font = ImageFont.truetype(font_path,96)
    label_w, label_h = font.getsize(label)
    img_target = Image.new('RGB', (label_w+10,label_h+10),(255,255,255))
    drawBrush = ImageDraw.Draw(img_target)
    drawBrush.text((0,0),label,fill=(0,0,0),font = font)
    img_target.save(os.path.join(save_dir,'%s_img_cont_reference.png' %label))
    return img_target

def save_single_image(save_dir,image_data,origin_image_uuid,content,label,aspect_ratio=1.0, width=256):
    #存在单个图片

    im = util.tensor2im(image_data)
    save_path=f"{save_dir}/{origin_image_uuid}"
    os.makedirs(save_path,exist_ok=True)
    save_path = os.path.join(save_path, f'{content}_{label}.png' )
    print(save_path)
    util.save_image(im, save_path, aspect_ratio=aspect_ratio)

def inferFontImage2target(opt):

    corpus = open(opt.corpusRoot, "r").read().splitlines()
    print('Totally %d strings in corpus.' % len(corpus))
    transform_img = lmdb_dataset.resizeKeepRatio((opt.imgW, opt.imgH))  
    infer_dataset=HackFontInferDataset(content_image_dir=opt.cont_refRoot,style_ttfRoot=opt.ttfRoot,target_transform=lmdb_dataset.resizeKeepRatio((opt.imgW, opt.imgH)),corpus=corpus)
    save_dir = opt.save_dir
    # data = {'A': img_style, 'B': img_content}
    model = create_model(opt)
    model.setup(opt)
    shutil.rmtree(save_dir,ignore_errors=True)
    os.makedirs(save_dir)
    if opt.eval:
        model.eval()
    model.eval()
    
    for font_id in range(len(infer_dataset.font_path)):
        for index in tqdm(range(len(infer_dataset))):     
            infer_dataset.font_id=font_id
            data=infer_dataset[index] 
            content_label=data['B_label']
            content2style_label=data['A_label']
            origin_png=data["content_rel_path"].split("/")[-1]
            save_file_name=f"{content_label}_{origin_png}"
            #save_path=data["save_path"]
            #image_uuid=data["image_uuid"]
            if len(content_label)==0:
                continue
            print(content_label)
            # if not is_contains_chinese(content_label):
            #     continue
            data = {'A': data['A'].unsqueeze(0), 'B': data['B'].unsqueeze(0)}
            
            model.set_single_input(data)
            model.forward()
            #continue
            #visuals =model.get_current_visuals()
            #save_single_image(save_dir, save_file_name,visuals,aspect_ratio=opt.aspect_ratio,width=opt.display_winsize)
            save_single_image(save_dir, model.img_print,f"fuhao",f"{index}-{font_id}-#","img_print",aspect_ratio=opt.aspect_ratio)
            save_single_image(save_dir, model.img_print2write,f"fuhao",f"{index}-{font_id}-#","img_print2write",aspect_ratio=opt.aspect_ratio)
            #print(font_id)
        if index%1000==0:
            
            import time
            time.sleep(20)
    #img_path = model.get_image_paths()
    print('preprocessing target image...')

if __name__ == '__main__':    
     
    # import debugpy
    # print("Enabling attach starts.")
    # debugpy.listen(address=('0.0.0.0', 9310))
    # debugpy.wait_for_client()
    # print("Enabling attach ends.")
    opt = InferOptions().parse() 
    # if opt.debug:
    #     import debugpy
    #     print("Enabling attach starts.")
    #     debugpy.listen(address=('0.0.0.0', 9310))
    #     debugpy.wait_for_client()
    #     print("Enabling attach ends.")
    transform_img = lmdb_dataset.resizeKeepRatio((opt.imgW, opt.imgH))  
    infer_dataset=HackInferDataset(content_image_dir=opt.cont_refRoot,style_ttfRoot=opt.ttfRoot,target_transform=lmdb_dataset.resizeKeepRatio((opt.imgW, opt.imgH)))
    inferFontImage2target(opt)
    exit(0) 
    # img_content = draw(opt.ttfRoot,opt.label,opt.save_dir)
    # #import pdb;pdb.set_trace()
    # img_content = transform_img(img_content).unsqueeze(0)
    # img_style = transform_img(Image.open(opt.sty_refRoot).convert('RGB')).unsqueeze(0)
    save_dir = opt.save_dir
    # data = {'A': img_style, 'B': img_content}
    model = create_model(opt)
    model.setup(opt)
    shutil.rmtree(save_dir,ignore_errors=True)
    os.makedirs(save_dir)
    if opt.eval:
        model.eval()
    model.eval()
    for index in tqdm(range(len(infer_dataset))):     
        data=infer_dataset[index] 
        content_label=data['B_label']
        origin_png=data["content_rel_path"].split("/")[-1]
        save_file_name=f"{content_label}_{origin_png}"
        #save_path=data["save_path"]
        image_uuid=data["image_uuid"]
        data = {'A': data['A'].unsqueeze(0), 'B': data['B'].unsqueeze(0)}
        model.set_single_input(data)
        
        model.output_cont_encode()
        #continue
        visuals =model.get_current_visuals()

        #save_single_image(save_dir, save_file_name,visuals,aspect_ratio=opt.aspect_ratio,width=opt.display_winsize)
        save_single_image(save_dir, model.img_print,content_label,content_label,"img_print",aspect_ratio=opt.aspect_ratio,width=opt.display_winsize)
        save_single_image(save_dir, model.img_print2write,image_uuid,content_label,"img_print2write",aspect_ratio=opt.aspect_ratio,width=opt.display_winsize)
    #img_path = model.get_image_paths()
    print('preprocessing target image...')
