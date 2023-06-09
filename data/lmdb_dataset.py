import random
import torch
from torch.utils.data import Dataset
from torch.utils.data import sampler
import torchvision.transforms as transforms
import lmdb
import six
import sys
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import string
from data import get_content_image_data

class ConcatLmdbDataset(Dataset):
    def __init__(self, dataset_list, batchsize_list, 
        ttfRoot=None, corpusRoot=None, transform_img=None,transform_target_img=None, alphabet=string.printable[:-6]):
        #import pdb;pdb.set_trace()
        assert len(dataset_list) == len(batchsize_list)

        if alphabet[-4:] == '.txt':
            alphabet_char = open(alphabet, 'r').read().splitlines()
        alphabet = ''.join(alphabet_char)

        self.corpus = open(corpusRoot, "r").read().splitlines()
        print('Totally %d strings in corpus.' % len(self.corpus))
        
        
        radical_dict = dict()
        total = open('data/IDS_dictionary.txt','r').read().splitlines()
        for line in total:
            char,radical = line.split(':')[0],line.split(':')[1]
            radical_dict[char] = radical
        
        if not os.path.isdir(ttfRoot):
            print('%s: the path to *.ttf is not a exist.' % (ttfRoot))
            sys.exit(0)        
        ttf = False
        self.font_path = []
        ttf_dir = os.walk(ttfRoot)
        for path, d, filelist in ttf_dir:
            for filename in filelist:
                if filename.endswith('.ttf') or filename.endswith('.ttc'):
                    self.font_path.append(path+'/'+filename)
                    ttf = True
        if not ttf:
            print('There is no ttf file in the dir.')
            sys.exit(0)
        else:
            print('Totally %d fonts for single character generation.' % len(self.font_path))
        # 这里临时加一块硬代码，把image部分加到里面
        batchsize_list.append(16)
        ds=fontAndImageDataset(style_database_root=dataset_list[0],
                image_content_path="tmp/hanimages/word2imgtop10",
                font_path=self.font_path,
                alphabet=alphabet,
                transform_img=transform_img,
                transform_target_img=transform_target_img,
                radical_dict=radical_dict
        )
        # hard code
        self.datasets = []
        self.prob = [batchsize / sum(batchsize_list) for batchsize in batchsize_list]
        for i in range(len(dataset_list)):
            print('For every iter: %s samples from %s' % (batchsize_list[i], dataset_list[i]))
            self.datasets.append(lmdbDataset(dataset_list[i], self.font_path, self.corpus, transform_img,transform_target_img, alphabet,radical_dict))
        # hard代码
        self.datasets.append(ds)
        
        #
        self.datasets_range = range(len(self.datasets))

    def __len__(self):
        return max([dataset.__len__() for dataset in self.datasets])

    def __getitem__(self, index):

        idx_dataset = np.random.choice(self.datasets_range, 1, p=self.prob).item()
        idx_sample = index % self.datasets[idx_dataset].__len__()
        #import pdb;pdb.set_trace()
        return self.datasets[idx_dataset][idx_sample]

class fontAndImageDataset(Dataset):
    # 直接从字体和文件夹中提供数据
    def __init__(self,style_database_root=None, image_content_path=None,font_path=None, corpus=None,
        transform_img=None,transform_target_img=None, alphabet=string.printable[:-6], radical_dict = None):
        assert transform_img != None
        self.env = lmdb.open(
            style_database_root,
            max_readers=1,
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False)
        if not self.env:
            print('cannot open lmdb from %s' % (style_database_root))
            sys.exit(0)

        with self.env.begin(write=False) as txn:
            nSamples = int(txn.get('num-samples'.encode()))
            self.nSamples = nSamples
        
        self.root = style_database_root
        self.transform_img = transform_img
        self.transform_target_img = transform_target_img
        self.image_content_nSamples = get_content_image_data(base_dir=image_content_path)
        self.corpus = corpus# 语料表
        self.alphabet = alphabet#字母表
        self.radical_dict = radical_dict# 偏旁部首字典

        # samples = get_content_image_data(base_dir=content_image_dir)
        # #import pdb;pdb.set_trace()
        # self.samples = samples
        # self.ids = [s[1] for s in samples]
        # self.target_transform = target_transform
        # self.loader = pil_loader
        # self.font_path = []
        # self.style_corpus = corpus# 语料表
        # if os.path.isfile(style_ttfRoot):
        #     self.font_path.append(style_ttfRoot)
        # else:
        #     ttf_dir = os.walk(style_ttfRoot)
        #     for path, d, filelist in ttf_dir:
        #         for filename in filelist:
        #             if filename.endswith('.ttf') or filename.endswith('.ttc') or filename.endswith('.otf'):
        #                 self.font_path.append(path+'/'+filename)
    
    def __len__(self):
        return self.nSamples
    

    def clear_lexicon(self,origin_lexicon):
        lexicon=origin_lexicon
        space_list = ['⿰','⿱','⿳','⿺','⿶','⿹','⿸','⿵','⿲','⿴','⿷','⿻']
        lexicon_list_old = lexicon.split()
        lexicon_list = []
        for i in lexicon_list_old:
            if i not in space_list:
                lexicon_list.append(i)
        lexicon = ' '.join(lexicon_list)# 这块就是所有去掉特殊字符之后⿰，都是偏旁部首。
        return lexicon
    def __getitem__(self, index):
        assert index <= len(self), 'index range error'
        index += 1
        # 这个是汉字图片
        content_label,rel_path,img_content = self.image_content_nSamples[index%len(self.image_content_nSamples)]# 扫描到一个汉字。
        lexicon_content = self.radical_dict[content_label]
        lexicon_content=self.clear_lexicon(lexicon_content)
        # 有50%的可能是，两者是一模一样的汉字，
        # 剩下的随机从一语料库中选一个汉字。
        if random.random()>=0.5:
            label_style = self.corpus[random.randint(0, len(self.corpus)-1)]
        else:
            label_style = content_label

        styleID=random.randint(0,len(self.font_path)-1)
        font = ImageFont.truetype(self.font_path[styleID], 64)
        lexicon_style = self.radical_dict[label_style]
        lexicon_style=self.clear_lexicon(lexicon_style)

        label_w, label_h = font.getsize(label_style)
        img_style = Image.new('RGB', (label_w, label_h), (255, 255, 255))
        drawBrush = ImageDraw.Draw(img_style)
        drawBrush.text((0, 0), label_style, fill=(0, 0, 0), font=font)


        img_content = self.transform_target_img(img_content)
        img_style = self.transform_img(img_style)

        return {'A': img_style, 'B': img_content, 'A_paths': (index-1) % len(self.image_content_nSamples), "B_paths":rel_path,'writerID': styleID,
        'A_label': label_style, 'B_label': content_label,'root':self.root,'A_lexicon':lexicon_style,'B_lexicon':lexicon_content}

            
class font2ImageDataset(Dataset):
    # 可以图片作为style也可以字体作为style。
    # 主要的目的是学习一个编码器。
    def __init__(self,style_database_root=None, image_content_path=None,font_path=None, corpus=None,
        transform_img=None,transform_target_img=None, alphabet=string.printable[:-6], radical_dict = None):
        assert transform_img != None
        self.env = lmdb.open(
            style_database_root,
            max_readers=1,
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False)
        if not self.env:
            print('cannot open lmdb from %s' % (style_database_root))
            sys.exit(0)

        with self.env.begin(write=False) as txn:
            nSamples = int(txn.get('num-samples'.encode()))
            self.nSamples = nSamples
        self.font_path=font_path
        self.root = style_database_root
        self.transform_img = transform_img
        self.transform_target_img = transform_target_img
        self.image_content_nSamples = get_content_image_data(base_dir=image_content_path)
        self.corpus = corpus# 语料表
        self.alphabet = alphabet#字母表
        self.radical_dict = radical_dict# 偏旁部首字典

    def __len__(self):
        return len(self.image_content_nSamples)
    

    def clear_lexicon(self,origin_lexicon):
        lexicon=origin_lexicon
        space_list = ['⿰','⿱','⿳','⿺','⿶','⿹','⿸','⿵','⿲','⿴','⿷','⿻']
        lexicon_list_old = lexicon.split()
        lexicon_list = []
        for i in lexicon_list_old:
            if i not in space_list:
                lexicon_list.append(i)
        lexicon = ' '.join(lexicon_list)# 这块就是所有去掉特殊字符之后⿰，都是偏旁部首。
        return lexicon
    def __getitem__(self, index):
        assert index <= len(self), 'index range error'
        index += 1
        # 这个是汉字图片
        if random.random()<1.0/(len(self.font_path)+1):# 1/(算上所有的字体+1)的概率图片作为content。
            content_label,rel_path,img_content = self.image_content_nSamples[index%len(self.image_content_nSamples)]# 扫描到一个汉字。
            lexicon_content = self.radical_dict[content_label]
            lexicon_content=self.clear_lexicon(lexicon_content)
            # 有50%的可能是，两者是一模一样的汉字，
            # 剩下的随机从一语料库中选一个汉字。
            if random.random()>=0.5:
                label_style = self.corpus[random.randint(0, len(self.corpus)-1)]
            else:
                label_style = content_label

            styleID=random.randint(0,len(self.font_path)-1)
            font = ImageFont.truetype(self.font_path[styleID], 64)
            lexicon_style = self.radical_dict[label_style]
            lexicon_style=self.clear_lexicon(lexicon_style)

            label_w, label_h = font.getsize(label_style)
            img_style = Image.new('RGB', (label_w, label_h), (255, 255, 255))
            drawBrush = ImageDraw.Draw(img_style)
            drawBrush.text((0, 0), label_style, fill=(0, 0, 0), font=font)

        else: # 字体画出的画作为content。
            label_style,rel_path,img_style=self.image_content_nSamples[index]
            styleID=len(self.font_path)# 字体上再加1个。
            lexicon_style = self.radical_dict[label_style]
            lexicon_style=self.clear_lexicon(lexicon_style)

            if random.random()<0.75:
                content_label = self.corpus[random.randint(0, len(self.corpus)-1)]
            else:
                content_label=label_style
            
            font_id=random.randint(0,len(self.font_path)-1)
            font = ImageFont.truetype(self.font_path[font_id], 64)
            lexicon_content = self.radical_dict[content_label]
            lexicon_content=self.clear_lexicon(lexicon_content)

            label_w, label_h = font.getsize(content_label)
            img_content = Image.new('RGB', (label_w, label_h), (255, 255, 255))
            drawBrush = ImageDraw.Draw(img_content)
            drawBrush.text((0, 0), content_label, fill=(0, 0, 0), font=font)

        img_content = self.transform_target_img(img_content)
        img_style = self.transform_img(img_style)

        return {'A': img_style, 'B': img_content, 'A_paths': (index-1) % len(self.image_content_nSamples), "B_paths":rel_path,'writerID': styleID,
        'A_label': label_style, 'B_label': content_label,'root':self.root,'A_lexicon':lexicon_style,'B_lexicon':lexicon_content}

class lmdbDataset(Dataset):

    def __init__(self, root=None, font_path=None, corpus=None,
        transform_img=None,transform_target_img=None, alphabet=string.printable[:-6], radical_dict = None):
        assert transform_img != None
        self.env = lmdb.open(
            root,
            max_readers=1,
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False)

        if not self.env:
            print('cannot open lmdb from %s' % (root))
            sys.exit(0)

        with self.env.begin(write=False) as txn:
            nSamples = int(txn.get('num-samples'.encode()))
            self.nSamples = nSamples
        
        self.root = root
        self.transform_img = transform_img
        self.transform_target_img = transform_target_img
        self.font_path = font_path
        self.corpus = corpus# 语料表
        self.alphabet = alphabet#字母表
        self.radical_dict = radical_dict# 偏旁部首字典
        

    def __len__(self):
        return self.nSamples

    def __getitem__(self, index):
        assert index <= len(self), 'index range error'
        index += 1
        with self.env.begin(write=False) as txn:
            
            label_key = 'label-%09d' % index
            label = str(txn.get(label_key.encode()).decode('utf-8'))
            if label == '##':
                return self[index + 1]

            lexicon_Key = 'lexicon-%09d' % index #词典信息
            lexicon = str(txn.get(lexicon_Key.encode()).decode('utf-8'))
            space_list = ['⿰','⿱','⿳','⿺','⿶','⿹','⿸','⿵','⿲','⿴','⿷','⿻']
            lexicon_list_old = lexicon.split()
            lexicon_list = []
            for i in lexicon_list_old:
                if i not in space_list:
                    lexicon_list.append(i)
            lexicon = ' '.join(lexicon_list)# 这块就是所有去掉特殊字符之后⿰，都是偏旁部首。
         
            img_key = 'image-%09d' % index
            imgbuf = txn.get(img_key.encode())
            buf = six.BytesIO()
            buf.write(imgbuf)
            buf.seek(0)
            try:
                img = Image.open(buf).convert('RGB')
            except IOError:
                print('Corrupted image for %d' % index)
                return self[index + 1]
            
            writerID_key = 'writerID-%09d' % index
            writerID = int(txn.get(writerID_key.encode()))
            font = ImageFont.truetype(self.font_path[random.randint(0,len(self.font_path)-1)], 64)
            label_target = self.corpus[random.randint(0, len(self.corpus)-1)]               
            lexicon_target = self.radical_dict[label_target]
            lexicon_target_list_old = lexicon_target.split()
            lexicon_target_list = []
            for i in lexicon_target_list_old:
                if i not in space_list:
                    lexicon_target_list.append(i)
            lexicon_target = ' '.join(lexicon_target_list)
            try:
                label_w, label_h = font.getsize(label_target)
                img_target = Image.new('RGB', (label_w, label_h), (255, 255, 255))
                drawBrush = ImageDraw.Draw(img_target)
                drawBrush.text((0, 0), label_target, fill=(0, 0, 0), font=font)
                # label_target 是从corpus语料表获取的，font也是根据font指定的，随机生成的。
                # label_target 是content，这个时候我就有一个疑问，如果我不知道content是什么的时候怎么办？
                # 
            except Exception as e:
                with open('failed_font.txt', 'a+') as f:
                    f.write(self.font_path[index % len(self.font_path)] + '\n')
                return self[index + 1]
            
            img_target = self.transform_target_img(img_target)
            img = self.transform_img(img)
            ###################### Target ######################

            return {'A': img, 'B': img_target, 'A_paths': (index-1) % len(self.corpus), 'writerID': writerID,
            'A_label': label, 'B_label': label_target,'root':self.root,'A_lexicon':lexicon,'B_lexicon':lexicon_target}
            
class imageDataset(Dataset):
    def __init__(self,style_database_root=None, image_content_path=None, corpus=None,
        transform_img=None,transform_target_img=None, alphabet=string.printable[:-6], radical_dict = None):
        assert transform_img != None
        self.env = lmdb.open(
            style_database_root,
            max_readers=1,
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False)

        if not self.env:
            print('cannot open lmdb from %s' % (style_database_root))
            sys.exit(0)

        with self.env.begin(write=False) as txn:
            nSamples = int(txn.get('num-samples'.encode()))
            self.nSamples = nSamples
        
        self.root = style_database_root
        self.transform_img = transform_img
        self.transform_target_img = transform_target_img
        self.image_content_nSamples = get_content_image_data(base_dir=image_content_path)
        self.corpus = corpus# 语料表
        self.alphabet = alphabet#字母表
        self.radical_dict = radical_dict# 偏旁部首字典

        # samples = get_content_image_data(base_dir=content_image_dir)
        # #import pdb;pdb.set_trace()
        # self.samples = samples
        # self.ids = [s[1] for s in samples]
        # self.target_transform = target_transform
        # self.loader = pil_loader
        # self.font_path = []
        # self.style_corpus = corpus# 语料表
        # if os.path.isfile(style_ttfRoot):
        #     self.font_path.append(style_ttfRoot)
        # else:
        #     ttf_dir = os.walk(style_ttfRoot)
        #     for path, d, filelist in ttf_dir:
        #         for filename in filelist:
        #             if filename.endswith('.ttf') or filename.endswith('.ttc') or filename.endswith('.otf'):
        #                 self.font_path.append(path+'/'+filename)
    
    def __len__(self):
        return self.nSamples
    

    def clear_lexicon(self,origin_lexicon):
        lexicon=origin_lexicon
        space_list = ['⿰','⿱','⿳','⿺','⿶','⿹','⿸','⿵','⿲','⿴','⿷','⿻']
        lexicon_list_old = lexicon.split()
        lexicon_list = []
        for i in lexicon_list_old:
            if i not in space_list:
                lexicon_list.append(i)
        lexicon = ' '.join(lexicon_list)# 这块就是所有去掉特殊字符之后⿰，都是偏旁部首。
        return lexicon
    def __getitem__(self, index):
        assert index <= len(self), 'index range error'
        index += 1
        with self.env.begin(write=False) as txn:
            
            label_key = 'label-%09d' % index
            label = str(txn.get(label_key.encode()).decode('utf-8'))
            if label == '##':
                return self[index + 1]

            lexicon_Key = 'lexicon-%09d' % index #词典信息
            lexicon = str(txn.get(lexicon_Key.encode()).decode('utf-8'))
            lexicon=self.clear_lexicon(lexicon)
            # space_list = ['⿰','⿱','⿳','⿺','⿶','⿹','⿸','⿵','⿲','⿴','⿷','⿻']
            # lexicon_list_old = lexicon.split()
            # lexicon_list = []
            # for i in lexicon_list_old:
            #     if i not in space_list:
            #         lexicon_list.append(i)
            # lexicon = ' '.join(lexicon_list)# 这块就是所有去掉特殊字符之后⿰，都是偏旁部首。
         
            img_key = 'image-%09d' % index
            imgbuf = txn.get(img_key.encode())
            buf = six.BytesIO()
            buf.write(imgbuf)
            buf.seek(0)
            try:
                img_style = Image.open(buf).convert('RGB')
            except IOError:
                print('Corrupted image for %d' % index)
                return self[index + 1]
            
            writerID_key = 'writerID-%09d' % index
            styleID = int(txn.get(writerID_key.encode()))


            content_label,rel_path,img_content = self.image_content_nSamples[index%len(self.image_content_nSamples)]
            lexicon_target = self.radical_dict[content_label]
            lexicon_target=self.clear_lexicon(lexicon_target)


            img_content = self.transform_target_img(img_content)
            img_style = self.transform_img(img_style)

            return {'A': img_style, 'B': img_content, 'A_paths': (index-1) % len(self.image_content_nSamples), "B_paths":rel_path,'writerID': styleID,
            'A_label': label, 'B_label': content_label,'root':self.root,'A_lexicon':lexicon,'B_lexicon':lexicon_target}
        
class resizeKeepRatio(object):

    def __init__(self, size, interpolation=Image.BILINEAR, 
        train=False):

        self.size = size
        self.interpolation = interpolation
        self.toTensor = transforms.ToTensor()
        self.train = train

    def __call__(self, img):

        if img.mode == 'L':
            img_result = Image.new("L", self.size, (255))
        elif img.mode =='RGB':
            img_result = Image.new("RGB",self.size, (255, 255, 255))
        else:
            print("Unknow image mode!")

        img_w, img_h = img.size

        target_h = self.size[1]
        target_w = max(1, int(img_w * target_h / img_h))

        if target_w > self.size[0]:
            target_w = self.size[0]

        img = img.resize((target_w, target_h), self.interpolation)
        begin = random.randint(0, self.size[0]-target_w) if self.train else int((self.size[0]-target_w)/2)
        box = (begin, 0, begin+target_w, target_h)
        img_result.paste(img, box)

        img = self.toTensor(img_result)
        img.sub_(0.5).div_(0.5)
        return img

def test_image_dataset():
    alphabet_char = open("data/alphabet.txt", 'r').read().splitlines()
    alphabet = ''.join(alphabet_char)
    radical_dict = dict()
    total = open('data/IDS_dictionary.txt','r').read().splitlines()
    for line in total:
        char,radical = line.split(':')[0],line.split(':')[1]
        radical_dict[char] = radical
    ds=imageDataset(style_database_root="data/train_set",
                image_content_path="tmp/hanimages/word2imgtop10",
                alphabet=alphabet,
                transform_img=resizeKeepRatio((128,128)),
                transform_target_img=resizeKeepRatio((128,128)),
                radical_dict=radical_dict
    )
    print(len(ds))
    print(ds[1])
if __name__ =='__main__':
    test_image_dataset()
    dataset = ConcatLmdbDataset(
        dataset_list = ['data/train_set'],
        batchsize_list = [16],
        ttfRoot = 'data/font',
        corpusRoot = "data/char_set.txt",
        transform_img= resizeKeepRatio((128,128)),
        transform_target_img=resizeKeepRatio((128,128)),
        alphabet = "data/alphabet.txt",      
    )
    train_loader = torch.utils.data.DataLoader(
        dataset,batch_size =32,sampler =None,drop_last=True,num_workers = 0,shuffle=False
    )
    dataset_size = len(dataset)    # get the number of images in the dataset.
    print('The number of training images = %d' % dataset_size)
    for i, data in enumerate(train_loader):
        #import pdb;pdb.set_trace()
        print(data)