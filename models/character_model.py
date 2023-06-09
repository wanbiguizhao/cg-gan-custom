import torch
import itertools
from util.str_converter import strLabelConverterForAttention,AttnLabelConverter
from .base_model import BaseModel
from . import networks,unet
import numpy as np
import torch.nn.functional as F


def lexicontoid(length,writerid):
    #import pdb;pdb.set_trace()
    lexicon_writerID = torch.LongTensor(length.sum().item()).fill_(0)
    start = 0
    for i,len in enumerate(length):
        lexicon_writerID[start:start+len] = writerid[i].expand(len)
        start = start + len
    #import pdb;pdb.set_trace()
    return lexicon_writerID


class CHARACTERModel(BaseModel):

    @staticmethod
    def modify_commandline_options(parser, is_train=True):
        #import pdb;pdb.set_trace()
        parser.set_defaults(no_dropout=True)  # default CycleGAN did not use dropout
        if is_train:
            parser.add_argument('--lambda_loc', type=float, default=0.1, help='weight for local D')
            parser.add_argument('--lambda_Lcontent', type=float, default=10.0, help='weight for Loss_G_content')                       
        return parser    
    
    
    def __init__(self, opt):
        BaseModel.__init__(self, opt)
        # specify the training losses you want to print out. The training/test scripts will call <BaseModel.get_current_losses>
        self.loss_names = ['D', 'D_lexicon','D_ID','D_radical_ID','unetD_real','unetD_middle_real','D_real_lexicon_feat','unetD_fake','unetD_middle_fake','D_fake_lexicon_feat',
                            'G', 'G_lexicon','G_ID','G_radical_ID','unetG','unetG_middle','G_lexicon_feat','G_idt','G_cont_idt']
        # self.loss_names = ['D', 'unetD_real','unetD_middle_real','unetD_fake','unetD_middle_fake',
        #                      'G', 'unetG','unetG_middle','G_idt','G_cont_idt','G_L1']
        
        # specify the images you want to save/display. The training/test scripts will call <BaseModel.get_current_visuals>
        visual_names_A = ['img_print', ]
        visual_names_B = ['img_print2write','img_write']
        self.visual_names = visual_names_A + visual_names_B
        
        # specify the models you want to save to the disk. The training/test scripts will call <BaseModel.save_networks> and <BaseModel.load_networks>.
        if self.isTrain:
            self.model_names = ['StyleEncoder', 'ContentEncoder', 'decoder', 'D']
        else:  # during test time, only load Gs
            self.model_names = ['StyleEncoder', 'ContentEncoder', 'decoder']
        
        # define networks
        self.netContentEncoder = unet.content_encoder(G_ch=opt.G_ch).cuda()# 内容编码的模型，
        self.netStyleEncoder = unet.style_encoder_textedit_addskip(G_ch = opt.G_ch).cuda()
        self.netdecoder = unet.decoder_textedit_addskip(G_ch = opt.G_ch, nEmbedding=1024).cuda()
        
        if self.isTrain:  # define discriminators
                       
            self.radical_path = opt.dictionaryRoot
            alphabet_radical = open(self.radical_path).read().splitlines()

            if opt.alphabet[-4:] == '.txt':
                alphabet_char = open(opt.alphabet, 'r').read().splitlines()
            #alphabet_char = ''.join(alphabet_char) 2023-05-08 注释掉，需要保留特殊字符
            # 
            self.netD = networks.define_D(len(alphabet_char)+1, opt.input_nc,opt.hidden_size,len(alphabet_char)+2,opt.dropout_p,opt.max_length,opt.D_ch,
                                            opt.num_writer,opt.norm, opt.init_type, opt.init_gain, self.gpu_ids,iam = False)# 这块生成的是判别器，主要是评分使用的。
            # len(alphabet_char)+1 这个参数没有使用。
            # len(alphabet_char)+2 这个属于输出使用，用于预测输出的笔画类型。
            self.converterATT = strLabelConverterForAttention(alphabet_char)# ?似乎没有被使用过。
            self.converter = AttnLabelConverter(alphabet_char)
            self.criterionGAN = networks.GANLoss(opt.gan_mode).to(self.device)  # define GAN loss.
            # self.criterionunetD =networks.unetDisLoss().to(self.device)
            self.criterionD =networks.DisLoss().to(self.device)# 判断D网络能不能区分真假图片。
            self.criterionIdt = torch.nn.L1Loss()
            self.criterionCls = torch.nn.CrossEntropyLoss()
            
            self.optimizer_G = torch.optim.Adam(itertools.chain(self.netContentEncoder.parameters(), 
                self.netStyleEncoder.parameters(),self.netdecoder.parameters()), lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizer_D = torch.optim.Adam(self.netD.parameters(), 
                lr=opt.lr, betas=(opt.beta1, 0.999))
            self.optimizers.append(self.optimizer_G)
            self.optimizers.append(self.optimizer_D)
                        

    def set_input(self, input): 
        # import pdb;pdb.set_trace()
        self.img_write = input['A'].to(self.device)
        self.img_print = input['B'].to(self.device)
        self.image_paths = input['B_label']
        self.writerID = input['writerID']
        self.paths = input['A_paths']
        
        if 'val' in input.keys():
            self.iseval = True
        else:
            self.iseval = False
                
        if self.isTrain and not self.iseval:
            
            self.label_A = input['A_label']
            self.label_B = input['B_label']
            self.lexicon_A = input['A_lexicon']
            self.lexicon_B = input['B_lexicon']
            self.new_lexicon_A,self.new_lexicon_A_length = self.converter.encode(self.lexicon_A)
            self.new_lexicon_B,self.new_lexicon_B_length = self.converter.encode(self.lexicon_B)
            #生成每个字体的部首对应的样式。
            self.lexicon_A_writerID = lexicontoid(self.new_lexicon_A_length,self.writerID).cuda()
            self.lexicon_B_writerID = lexicontoid(self.new_lexicon_B_length,self.writerID).cuda()
            
            self.new_lexicon_A = self.new_lexicon_A.cuda()
            self.new_lexicon_B = self.new_lexicon_B.cuda() 
            
            self.writerID = self.writerID.cuda()
    
    def set_single_input(self,input):

        self.img_write = input['A'].to(self.device)# style image
        self.img_print = input['B'].to(self.device)# content image 来自原语料数据txt
        self.visual_names = ['img_print2write','img_print']

    def forward(self):

        """Run forward pass; called by both functions <optimize_parameters> and <test>."""
        #import pdb;pdb.set_trace()
        # img_write 是style  A
        # img_print 是 content
        self.style_emd,self.style_fc,self.residual_features_style = self.netStyleEncoder(self.img_write)# self.style_emd,self.style_fc 的关系style_fc在style_emd的基础上做了自适应平均，变成了1，1的矩阵。
        self.cont,self.residual_features = self.netContentEncoder(self.img_print)# img_print is content image self.cont [bs,ch=1024,h=4,w=4]
        # self.residual_features [torch.Size([4, 3, 128, 128]), torch.Size([4, 64, 64, 64]), torch.Size([4, 128, 32, 32]), torch.Size([4, 256, 16, 16]), torch.Size([4, 512, 8, 8])]
        self.img_print2write = self.netdecoder(self.cont,self.residual_features,self.style_emd,self.style_fc,self.residual_features_style)
        # 生成器基本上是和图片有关系，这点非常重要。
    
    def output_cont_encode(self):
        
        with torch.no_grad():
            self.cont,self.residual_features = self.netContentEncoder(self.img_print)#
            return self.cont.reshape(-1)


        
    def backward_D_basic(self, netD, real, fake):

        lambda_loc = self.opt.lambda_loc
        # Real
        pred_radical_real, loss_D_real_lexicon, out_real, writerID_real, radical_writerID_real =netD(real, self.new_lexicon_A,self.new_lexicon_A_length)       
        # self.loss_unetD_real, self.loss_unetD_middle_real = self.criterionunetD(out_real,bottleneck_out_real,True)
        self.loss_unetD_middle_real = self.criterionD(out_real,True)
        self.loss_D_real_lexicon_feat = self.criterionGAN(pred_radical_real,True)
        loss_D_real = self.loss_unetD_middle_real + self.loss_D_real_lexicon_feat
        loss_D_ID = self.criterionCls(writerID_real, self.writerID)
        loss_D_radical_ID = self.criterionCls(radical_writerID_real, self.lexicon_A_writerID)
       
        # Fake
        pred_radical_fake, _, out_fake, _, _= netD(fake.detach(), self.new_lexicon_B, self.new_lexicon_B_length)        
        # self.loss_unetD_fake,self.loss_unetD_middle_fake = self.criterionunetD(out_fake,bottleneck_out_fake,False)
        self.loss_unetD_middle_fake = self.criterionD(out_fake,False)
        self.loss_D_fake_lexicon_feat = self.criterionGAN(pred_radical_fake,False)
        loss_D_fake = self.loss_unetD_middle_fake + self.loss_D_fake_lexicon_feat        
        #loss_D_fake = self.loss_unetD_fake * lambda_loc + self.loss_unetD_middle_fake 
        loss_D = (loss_D_real + loss_D_fake) * 0.5
        (loss_D + loss_D_real_lexicon + loss_D_ID + loss_D_radical_ID ).backward()
        
        return loss_D, loss_D_real_lexicon, loss_D_ID, loss_D_radical_ID

    def backward_D(self):

        self.loss_D, self.loss_D_lexicon, self.loss_D_ID, self.loss_D_radical_ID = self.backward_D_basic(self.netD, self.img_write, self.img_print2write)
        
    def backward_G(self):
        
        lambda_loc = self.opt.lambda_loc
        lambda_content = self.opt.lambda_Lcontent
        #输入 判别器是生成的img_print2write图片，图片汉字对应的偏旁部首，图片汉字对应的
        #预测的部首 ，loss 偏旁部首的损失  ，out 是D网络的判别输出  ，字的类型， 偏旁部首的ID
        pred_radical, loss, out, writerID, radical_wrtiterID = self.netD(self.img_print2write, self.new_lexicon_B, self.new_lexicon_B_length)        
        # 预测的部首，损失，out->cnn提取的特征，风格特征，部首的风格特征。
        #loss_G
        # self.loss_unetG, self.loss_unetG_middle = self.criterionunetD(out, bottleneck_out, True)
        self.loss_unetG_middle = self.criterionD(out, True)
        # self.loss_G = self.loss_unetG* lambda_loc + self.loss_unetG_middle
                
        self.loss_G_lexicon_feat = self.criterionGAN(pred_radical,True)
        self.loss_G_lexicon = loss
        self.loss_G = self.loss_unetG_middle +  self.loss_G_lexicon_feat
        #loss_ID
        self.loss_G_ID = self.criterionCls(writerID, self.writerID)
        self.loss_G_radical_ID = self.criterionCls(radical_wrtiterID, self.lexicon_B_writerID)
        #loss_cont_idt
        self.cont_g, _ = self.netContentEncoder(self.img_print2write)
        self.loss_G_cont_idt = self.criterionIdt(self.cont, self.cont_g) * lambda_content # 计算对于内容编码的损失。cont 来源于B。
        #loss_idt
        self.cont_w,self.residual_features_w = self.netContentEncoder(self.img_write)# 对style image的内容进行编码，
        img_idt = self.netdecoder(self.cont_w,self.residual_features_w,self.style_emd,self.style_fc,self.residual_features_style)
        self.loss_G_idt = self.criterionIdt(img_idt, self.img_write)# 使用自己的图片，重新生成的图片，应该尽量奶盖保证一致，模型的稳定性
        
        (self.loss_G + self.loss_G_idt+self.loss_G_lexicon + self.loss_G_ID +self.loss_G_radical_ID+self.loss_G_cont_idt).backward()
               

    def optimize_parameters(self):

        # forward
        self.forward()      # compute fake images and reconstruction images.
        # G
        self.set_requires_grad([self.netD], False)
        self.optimizer_G.zero_grad()  # set G's gradients to zero
        self.backward_G()             # calculate gradients for G
        self.optimizer_G.step()       # update G's weights
        # D
        self.set_requires_grad([self.netD], True)
        self.optimizer_D.zero_grad()   # set D's gradients to zero
        self.backward_D()      # calculate gradients for D
        self.optimizer_D.step()  # update D's weights
        
        


