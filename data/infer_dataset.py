# 提供content的图片由图片直接提供，而不是由提供。
from torch.utils.data import Dataset
from PIL import Image, ImageDraw, ImageFont
import os
import random
from data.val_dataset import draw
try:
    from lmdb_dataset import resizeKeepRatio
except:
    from data.lmdb_dataset import resizeKeepRatio
from util.font2img import is_contains_chinese
from glob import glob
def make_dataset(dir):
    # 存放希望变成style的图片。
    path_list = open(dir,'r').read().splitlines()
    images = []
    #import pdb;pdb.set_trace()
    for img_path in path_list:
        label =img_path.split('/')[-1].split('.')[0].split('_')[-1]
        id = int(img_path.split('/')[-2])
        item = (img_path,id,label)
        images.append(item)
    return images

def get_content_image_data(image_file_path=None,base_dir=None):
    """
    获取目录，获得图片，该图片是OCR目前不能识别的图片
    image_file_path 记录content图片的基本信息的文件路劲
    数据格式:汉字\t图片路径
    or 
    base_dir 提供汉字图片的文件夹
   格式是：汉字/对应的图片 
    """
    result=[]
    if base_dir:
        for hanzi_dir in os.listdir(base_dir):
            if "@" not in hanzi_dir:
                continue
            prefix,han=hanzi_dir.split("@")
            if not  is_contains_chinese(han):
                continue
            # 找到里面的图片
            for image_path in glob(os.path.join(base_dir,hanzi_dir,"*.png")):
                result.append([han,image_path[len(base_dir)+1:],pil_loader(image_path)])
            #print(result[-1])
        return result
    assert os.path.exists(image_file_path)
    assert os.path.isfile(image_file_path)
    image_list=[]
    image_file_info=open(image_file_path,"r").read().splitlines()
    
    


def pil_loader(path):
    # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
    with open(path, 'rb') as f:
        img = Image.open(f)
        return img.convert('RGB')
class InferDataset(Dataset):
    def __init__(self,content_image_dir,style_ttfRoot,target_transform = resizeKeepRatio((128, 128))):
        #import pdb;pdb.set_trace()
        samples = get_content_image_data(base_dir=content_image_dir)
        #import pdb;pdb.set_trace()
        self.samples = samples
        self.ids = [s[1] for s in samples]
        self.target_transform = target_transform
        self.loader = pil_loader
        self.font_path = []
        if os.path.isfile(style_ttfRoot):
            self.font_path.append(style_ttfRoot)
        else:
            ttf_dir = os.walk(style_ttfRoot)
            for path, d, filelist in ttf_dir:
                for filename in filelist:
                    if filename.endswith('.ttf') or filename.endswith('.ttc') or filename.endswith('.otf'):
                        self.font_path.append(path+'/'+filename)
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, index):
        label,rel_path,img_content = self.samples[index]
        img_content=self.target_transform(img_content)# 这个是可以提前做，避免训练的时候做
        # img_style = self.loader(f"tmp/images/{path}")
        # if self.target_transform is not None:
        #     img_style = self.target_transform(img_style)
        content_target = label 
        
        # 從字體中画一个图片作为样式参考
        font_path = self.font_path[random.randint(0,len(self.font_path)-1)]
        style_label="聯"
        img_style = draw(font_path,style_label)
        img_style = self.target_transform(img_style)
        styleID = id             
        return {'A': img_style, 'B': img_content, 'A_paths': index, 'writerID': styleID,"content_rel_path":rel_path,
            'A_label': style_label, 'B_label': content_target, 'val':True}

if __name__=="__main__":
    val=InferDataset()
    pass
