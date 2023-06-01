# 把原来128的图片调整到指定大小。
from PIL import Image, ImageDraw, ImageFont
import cv2 as cv
import numpy
import os ,shutil

from tqdm import tqdm
from font2img import is_contains_chinese
def smart_make_dirs(dir_paths,remove=True):
    if not os.path.exists(dir_paths):
        os.makedirs(dir_paths)
    else:
        if remove:
            shutil.rmtree(dir_paths)
    
def do_resize_image(image_path,h_size=64,w_size=64):
    # 采取一部分白边。
    h=h_size
    w=w_size
    origin_image=Image.open(image_path).convert('L')
    crop_image=origin_image.crop([5,5,123,123]).resize([h,w],resample=Image.LANCZOS)# 两边都裁剪一点，排除生成的比较乱的情况。
    #crop_image.show()
    cv_image=numpy.array(crop_image)
    blur = cv.GaussianBlur(cv_image,(5,5),0)
    _,th_image = cv.threshold(blur,0,255,cv.THRESH_BINARY+cv.THRESH_OTSU)
    
    l,r,u,d=0,w-1,h-1,0
    while  l<r and sum(th_image[:,l])==255*h:
        l+=1
    while l<r and sum(th_image[:,r])==255*h:
        r-=1
    while d<u and sum(th_image[d,:])==255*w:
        d+=1
    while d<u and sum(th_image[u,:])==255*w:
        u-=1
    #crop_image.crop([ max(0,d-1),max(0,l-1),min(h,u+1),max(w,r+1)]).show()
    return crop_image.crop([max(0,l-1),max(0,d-1),min(w,r+1),min(h,u+1)])
    #cv("image",cv_image[ d : u+1, max(l-1,0):min( w,r+1+1)] )# 上下左右各留了2像素

def pipeline01():
    # convert {basic_image_dir} from size 128 to  55
    # save to {resize_image_dir}
    h_size,w_size=55,55
    basic_image_dir="tmp/infer_images"
    resize_image_dir="tmp/infer_images_resize"
    smart_make_dirs(resize_image_dir)
    target_image_info_list=[]
    # 收集信息
    for dir_name in tqdm(os.listdir(basic_image_dir),desc="收集图片"):
        han=dir_name
        assert is_contains_chinese(han)
        for png_name in os.listdir(f"{basic_image_dir}/{dir_name}"):
            png_path=f"{basic_image_dir}/{dir_name}/{png_name}"
            target_image_info_list.append({
                "png_name":png_name,
                "png_path":png_path,
                "han":han
            })
    for image_info in tqdm(target_image_info_list,desc="重新调整图片分辨率"):
        pil_image=do_resize_image(image_info["png_path"],h_size,w_size)
        save_dir=f"{resize_image_dir}/{image_info['han']}"
        smart_make_dirs(save_dir,remove=False)
        pil_image.save(f"{save_dir}/{image_info['png_name']}")

            

if __name__=="__main__":
    pipeline01() 

# do_resize_image("tmp/infer_images/僔/0-僔#_img_print.png")
# do_resize_image("tmp/infer_images/僔/1-僔#_img_print.png")
# do_resize_image("tmp/infer_images/僔/2-僔#_img_print.png")
# do_resize_image("tmp/infer_images/僔/3-僔#_img_print.png")
# do_resize_image("tmp/infer_images/僔/0-僔#_img_print2write.png")

# do_resize_image("tmp/infer_images/僔/1-僔#_img_print2write.png")

# do_resize_image("tmp/infer_images/僔/2-僔#_img_print2write.png")
# do_resize_image("tmp/infer_images/僔/3-僔#_img_print2write.png")
# cv.waitKey(100000)
# print("hehe")