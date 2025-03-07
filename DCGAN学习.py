

#1.创建一个out文件夹来保存训练的中间结果
import copy
import os
import time


#2导入所需的包
import random
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torch.optim as optim
import torchvision.datasets as dset
import torchvision.transforms as transforms
import numpy as np
import torchvision.utils as vutils
import matplotlib.pyplot as plt
from netG import Generator
from netD import Discriminator
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


#3.基本参数配置
#设置一个随机种子，方便进行可重复的实验
manualSeed=999
print("Random seed=",manualSeed)
random.seed(manualSeed)
torch.manual_seed(manualSeed)

#数据集所在的路径
dataroot=r".\project1\data"
#数据加载进程数
workers=0
#batch size大小
batch_size=32
#图片的大小
image_size=128

#图片的通道数
nc=3
#一张图片的随机噪声
nz=100
#生成器generator的特征大小
ngf=64
#判别器discrimination的特征大小
ndf=64
#训练的次数
num_epoch=79
lr=0.0003
beta1=0.5#数据优化-待学习
device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

#4.导入数据集
dataset=dset.ImageFolder(root=dataroot,
                         transform=transforms.Compose([
                             transforms.Resize(image_size),
                             transforms.CenterCrop(image_size),
                             transforms.ToTensor(),
                             transforms.Normalize((0.5,0.5,0.5),(0.5,0.5,0.5))
                         ]))

dataloader=DataLoader(dataset=dataset,batch_size=batch_size,shuffle=True,num_workers=workers)


#5.查看一下数据长啥样
real_batch=next(iter(dataloader))#next() 返回迭代器的下一个项目。
# next() 函数要和生成迭代器的 iter() 函数一起使用。
#由于datalader包含特征和标签，所以返回值是列表类型list[2,],list【0】表示特征，list【1】表示标签都是tenso类型
plt.figure(figsize=(8,8))#设置画布，画布大小figsize
plt.axis("off")#关闭坐标轴
plt.title("train images")
#imshow()其实就是将数组的值以图片的形式展示出来
plt.imshow(np.transpose(vutils.make_grid(real_batch[0].to(device)[:64],padding=2,normalize=True).cpu(),(1,2,0)))
#transpose 交换维度例如将（3,64,64）交换为（64,64,3）
#make_grid()把多个图片放在一张图上
plt.show()


#7.初始化生成器和判别器
#实例化生成器
netG=Generator().to(device)
#netG.apply(weights_init)
print("netG",netG)

#实例化判别器
netD=Discriminator().to(device)
#netD.apply(weights_init)
print("netD=",netD)


#8.定义损失函数
criterion=nn.BCELoss()


#9.开始训练
#创建一批噪声数据用来生成
fixed_noise=torch.randn(size=(64,nz,1,1),device=device)#(64,100,1,1) 用于每次观察图像生成的如何
#建立真假标签值
real_label=1.0
fake_label=0.0
#建立优化模型
optimizer_D=optim.Adam(netD.parameters(),lr=lr,betas=(beta1,0.999))
optimizer_G=optim.Adam(netG.parameters(),lr=lr,betas=(beta1,0.999))

#建立一些列表跟踪进程
img_list=[]
G_losses=[]
D_losses=[]
iters=0
print("starting Training 开始训练")
for epoch in range(num_epoch):
    import time
    start=time.time()
    for i ,data in enumerate(dataloader,0):
        #1.跟新判别器D (1) Update D network: maximize log(D(x))
        # + log(1 - D(G(z)))
        #1.1真实图片的损失
        netD.zero_grad()
        real_cpu=data[0].to(device)#(64,3,64,64)
        b_size=real_cpu.size(0)#(64)
        label=torch.full((b_size,),real_label,device=device)#64个1
        output=netD(real_cpu).view(-1)#64*1*1*1--64
        D_real_loss=criterion(output,label)
        D_real_loss.backward()
        D_x=output.mean().item()#
        #1.2fake图片的损失
        noise=torch.randn(b_size,nz,1,1,device=device)#64*100*1*1
        fake=netG(noise)
        label.fill_(fake_label)#
        output=netD(fake.detach()).view(-1)
        D_fake_loss=criterion(output,label)
        D_fake_loss.backward()
        D_G_z1=output.mean().item()
        D_loss=(D_real_loss+D_fake_loss)
        optimizer_D.step()

        #2.跟新generator的network(2) Update G network: maximize log(D(G(z)))
        netG.zero_grad()
        label.fill_(real_label)
        output=netD(fake).view(-1)
        G_loss=criterion(output,label)
        G_loss.backward()
        D_G_z2=output.mean().item()
        optimizer_G.step()
        #输出训练结果
        if i %20==0:
            print("epoch:",epoch,"num_epoch:",num_epoch,
                  "batch:",i,
                  "D_real_loss:",D_real_loss.item(),
                  "D_fake_loss:",D_fake_loss.item(),
                  "D_loss:",D_loss.item(),
                  "G_loss:",G_loss.item())
        G_losses.append(G_loss.item())
        D_losses.append(D_loss.item())

        #检查fixe_noise在generator上的结果
        if(iters%20==0) or (i==len(dataloader)-1):
            with torch.no_grad():
                fake=netG(fixed_noise).detach().cpu()
            img_list.append(vutils.make_grid(fake,padding=2,normalize=True))
            i=vutils.make_grid(fake,padding=2,normalize=True)
            fig=plt.figure(figsize=(8,8))
            plt.imshow(np.transpose(i,(1,2,0)))
            plt.axis("off")
            root=".\project1\out\\"
            plt.savefig(root+str(epoch)+"_"+str(iters)+".png")
            plt.close(fig)
        iters+=1
    print("time=",time.time()-start)


#10.绘制损失曲线
plt.figure(figsize=(10,5))
plt.title("generator and Discriminator loss During Training")
plt.plot(G_losses,label="G")
plt.plot(D_losses,label="D")
plt.xlabel("iterations")
plt.ylabel("loss")
plt.legend()
plt.show()


#11.真假图片对比
# Grab a batch of real images from the dataloader
# real_batch = next(iter(dataloader))

# Plot the real images
plt.figure(figsize=(15,15))
plt.subplot(1,2,1)
plt.axis("off")
plt.title("Real Images")
plt.imshow(np.transpose(vutils.make_grid(real_batch[0].to(device)[:64], padding=5, normalize=True).cpu(),(1,2,0)))

# Plot the fake images from the last epoch
plt.subplot(1,2,2)
plt.axis("off")
plt.title("Fake Images")
plt.imshow(np.transpose(img_list[-1],(1,2,0)))
plt.show()


#保存训练好的模型
torch.save(netG,"./netg"+str(num_epoch)+".pt")
torch.save(netD,"./netd"+str(num_epoch)+".pt")













