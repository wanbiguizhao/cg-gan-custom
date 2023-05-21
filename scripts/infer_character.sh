set -ex
CUDA_VISIBLE_DEVICES=0 python infer.py \
--checkpoints_dir tmp \
--ttfRoot tmp/font/ \
--save_dir tmp/infer_images \
--cont_refRoot tmp/hanimages/word2imgtop10 \
--sty_refRoot images_iam/img_sty_reference.png \
--name exp \
--model character \
--no_dropout \
--batch_size 1 \
--imgH 128 \
--imgW 128 \
--gpu_ids 0 \
--epoch latest \
--G_ch 64 \
