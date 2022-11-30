import torch
import torchvision
from torchvision import datasets, transforms
import time

transform = transforms.Compose([transforms.Resize((128,128)),
                                 transforms.ToTensor()])
dataset = datasets.ImageFolder('./Born', transform=transform)
dataloader = torch.utils.data.DataLoader(dataset, 
                                         batch_size=64, 
                                         num_workers=40, 
                                         persistent_workers=True, 
                                         shuffle=False)

for ii in range(10):
    a = time.time()
    _ = next(iter(dataloader))
    b = time.time()
    print(b-a)
