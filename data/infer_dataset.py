# 提供content的图片由图片直接提供，而不是由提供。
from torch.utils.data import Dataset
import os
import random
from data.val_dataset import draw
try:
    from lmdb_dataset import resizeKeepRatio
except:
    from data.lmdb_dataset import resizeKeepRatio
from data import get_content_image_data,pil_loader
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


class InferDataset(Dataset):
    def __init__(self,content_image_dir,style_ttfRoot,target_transform = resizeKeepRatio((128, 128)),corpus=None, ):
        #import pdb;pdb.set_trace()
        samples = get_content_image_data(base_dir=content_image_dir)
        #import pdb;pdb.set_trace()
        self.samples = samples
        self.ids = [s[1] for s in samples]
        self.target_transform = target_transform
        self.loader = pil_loader
        self.font_path = []
        self.style_corpus = corpus# 语料表
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

class HackInferDataset(Dataset):
    def __init__(self,content_image_dir,style_ttfRoot,target_transform = resizeKeepRatio((128, 128)),corpus=None, ):
        #import pdb;pdb.set_trace()
        samples = get_content_image_data(image_file_path="image_low_score_info.txt")
        #import pdb;pdb.set_trace()
        self.samples = samples
        self.ids = [s[1] for s in samples]
        self.target_transform = target_transform
        self.loader = pil_loader
        self.font_path = []
        self.style_corpus = corpus# 语料表
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
        label,rel_path,img_content,image_uuid = self.samples[index]
        img_content=self.target_transform(img_content)# 这个是可以提前做，避免训练的时候做
        # img_style = self.loader(f"tmp/images/{path}")
        # if self.target_transform is not None:
        #     img_style = self.target_transform(img_style)
        content_target = label 
        
        # 從字體中画一个图片作为样式参考
        font_path = self.font_path[random.randint(0,len(self.font_path)-1)]
        style_label=label
        img_style = draw(font_path,style_label)
        img_style = self.target_transform(img_style)
        styleID = 0             
        return {'A': img_style, 'B': img_content, 'A_paths': index, 'writerID': styleID,"content_rel_path":rel_path,
            'A_label': style_label, 'B_label': content_target, 'val':True,"image_uuid":image_uuid}


class HackFontInferDataset(Dataset):
    #根据模型把字体转换成图片，。
    def __init__(self,content_image_dir,style_ttfRoot,target_transform = resizeKeepRatio((128, 128)),corpus=None, ):
        #import pdb;pdb.set_trace()
        samples = get_content_image_data(image_file_path="image_low_score_info.txt")
        #import pdb;pdb.set_trace()
        self.samples = samples
        self.ids = [s[1] for s in samples]
        self.target_transform = target_transform
        self.loader = pil_loader
        self.font_path = []
        self.style_corpus = corpus# 语料表
        if os.path.isfile(style_ttfRoot):
            self.font_path.append(style_ttfRoot)
        else:
            ttf_dir = os.walk(style_ttfRoot)
            for path, d, filelist in ttf_dir:
                for filename in filelist:
                    if filename.endswith('.ttf') or filename.endswith('.ttc') or filename.endswith('.otf'):
                        self.font_path.append(path+'/'+filename)
        self.font_id=0
    def __len__(self):
        return len(self.style_corpus)
    
    def __getitem__(self,index):


        label,rel_path,img_style,image_uuid = self.samples[random.randint(0,len(self.samples)-1)]# 做style
        style_label=label


        # 從字體中选择一个汉字作为参考
        content_target = self.style_corpus[index%len(self.style_corpus)] 
        
        #font_path = self.font_path[random.randint(0,len(self.font_path)-1)]
        font_path = self.font_path[self.font_id]
        img_content = draw(font_path,content_target)

        img_content=self.target_transform(img_content)
        img_style = self.target_transform(img_style)
        styleID = 0             
        return {'A': img_style, 'B': img_content, 'A_paths': index, 'writerID': styleID,"content_rel_path":rel_path,
            'A_label': style_label, 'B_label': content_target, 'val':True,"image_uuid":image_uuid}

if __name__=="__main__":
    val=InferDataset()
    pass
