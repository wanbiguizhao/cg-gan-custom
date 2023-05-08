# 把IDS_dictionary.txt 中所有的笔画都拆分出来。
import os
import argparse
def default_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-dict-file', type=str,dest="src_dict", default=None, help='汉字2笔画的文件')
    parser.add_argument('--dst-file', type=str, dest="dst_file",default=None, help='笔画文件')
    return parser 

def convert(src_dict,dst_file):
    """
    提取所有汉字的笔画
    """
    assert os.path.exists(src_dict)
    #assert os.path.isfile(src_dict)
    radical_set=set()
    
    with open(src_dict,"r") as src_file,open(dst_file,"w") as dst_file:
        for line in src_file.read().splitlines():
            if len(line)==0:
                continue
            radical_set.update(line.split(':')[1].split(' '))
        list_character=list(radical_set)
        dst_file.write("\n".join(sorted(list_character)))

if __name__ == "__main__":
    parser=default_args_parser()
    args = parser.parse_args()
    convert(src_dict=args.src_dict,dst_file=args.dst_file)
    #convert("/home/liukun/share/font/","tmp/images")
    

