import os 
from glob import glob
from PIL import Image


from util.font2img import is_contains_chinese
def get_content_image_data(image_file_path=None,base_dir=None):
    """
    获取目录，获得图片，该图片是OCR目前不能识别的图片
    image_file_path 记录content图片的基本信息的文件路劲
    数据格式:汉字\t图片路径
    or 
    base_dir 提供汉字图片的文件夹
   格式是：汉字/对应的图片 
   return: [汉字，相对路径，图片PIL对象 ]
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