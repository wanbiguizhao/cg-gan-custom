import lmdb
from PIL import Image, ImageDraw, ImageFont
import six
db=lmdb.open(
            "/home/liukun/Downloads/IAM/train/train_IAM/",
            max_readers=1,
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False)
with db.begin(write=False) as txn:
    cursor =txn.cursor()
    it=iter(cursor)
    print(it)
    it=cursor.iternext(keys=True,values=True)
    print(it)
    for idx, data in enumerate(cursor.iternext_dup(keys=True)):
        imageKey=data[0].decode('utf-8')
        #imageKey = 'image-%09d' % str(index)
        #print("%d'th value for 'foo': %s" % (idx, data))
        imgbuf=txn.get(imageKey.encode())
        buf = six.BytesIO()
        buf.write(imgbuf)
        buf.seek(0)
        try:
            img = Image.open(buf).convert('RGB')
        except IOError:
            print('Corrupted image for %d' % 2)
        img.show()
