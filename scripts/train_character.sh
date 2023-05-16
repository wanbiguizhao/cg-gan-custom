set -ex
CUDA_VISIBLE_DEVICES=0 python train.py \
--dataroot data/train_set \
--ttfRoot data/font \
--corpusRoot data/char_set.txt \
--alphabet data/alphabet.txt \
--dictionaryRoot data/dictionary.txt \
--name exp \
--model character \
--no_dropout \
--batch_size 2 \
--imgH 128 \
--imgW 128 \
--num_writer 399 \
--num_writer_emb 256 \
--gpu_ids 0 \
--lr 0.0001 \
--lr_decay_iters 30 \
--niter_decay 30 \
--G_ch 64 \
--D_ch 16 \
--max_length 64 \
--hidden_size 256 \
--val_num 10 \
--val_seenstyleRoot data/seenstyle_oov.txt \
--val_unseenstyleRoot data/unseenstyle_oov.txt \
--debug
