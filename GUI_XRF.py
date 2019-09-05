#General GUI
import numpy as np
import scipy.io as scio
import os
import h5py
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
import view_maps as vem
from PIL import Image, ImageTk

root = tk.Tk()
root.title('main_GUI')
root.geometry('900x350')
#load default parameters
def loadMat(df):
    names = globals()
    for i in df:
        if i[0]!='_':
            names[i] = df[i].squeeze()
            if names[i].shape == ():
                names[i] = names[i].reshape(1)[0]

df = scio.loadmat(os.getcwd()+'/data/Default_parameter.mat')
loadMat(df)

All_Elements = ['H','He','Li','Be','B','C','N','O','F','Ne',
                'Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca',
                'Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn',
                'Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr',
                'Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn',
                'Sb','Te','I','Xe','Cs','Ba','La','Ce','Pr','Nd',
                'Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb',
                'Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg',
                'Tl','Pb','Bi','Po','At','Rn','Fr','Ra','Ac','Th',
                'Pa','U','Np','Pu','Am']

def selectResult():
    filePath = filedialog.askopenfilename(initialdir = os.getcwd()+'/data',
                                   title = 'Select file',
                                   filetypes=([('mat files','*.mat')]))
    filename = filePath.split('/')[-1]
    if filename.split('_')[1] == 'result':
        info.set('Loading result...')
        df1 = scio.loadmat(filePath)
        loadMat(df1)
        fpath_mat.set(filePath)
        info.set('Successfully load result data! ! !'
                 +'\nNow you can view elements map or load XRF data cube.')
        resultFlag.set(1)
    else:
        msg.showwarning('Warning','Please select correct result file')

def selectXRF():
    filePath = filedialog.askopenfilename(initialdir = os.getcwd()+'/data',
                                   title = 'Select file',
                                   filetypes=([('mat files','*.mat')]))
    filename = filePath.split('/')[-1]
    if filename.split('_')[1] == 'datacube.mat':
        info.set('Loading result...')
        df = h5py.File(filePath)
        data_patch_cube = np.transpose(df['data_patch_cube'][:])
        fpath_raw.set(filePath)
        info.set('Successfully load XRF data cube! ! !'
                 +'\nNow you can view elements map or specific pixel elements.')
        XRFFlag.set(1)
    else:
        msg.showwarning('Warning','Please select correct XRF data cube file')


def reset():
    fpath_mat.set('')
    fpath_raw.set('')
    selectElements.set('')
    confidenceThreshold.set(0.0)
    resultFlag.set(0)
    XRFFlag.set(0)
    pixelX.set(1)
    pixelY.set(1)
    info.set('Please select result data')

def vemFunc():
    if resultFlag.get():
        if selectElements.get():
            if 0<int(pixelX.get())<=column_num and 0<int(pixelY.get())<=row_num:
                atomic_number_chosen=eval('['+str(selectElements.get())+']')
                vem.view_maps(atomic_number_chosen,
                              confidenceThreshold.get(),
                              confidence_map,
                              elements_interested,
                              quality_map,
                              column_num,row_num,
                              All_Elements,
                              line.get(),
                              int(pixelX.get()),int(pixelY.get()))
            else:
                msg.showwarning('Warning',
                                'Please do not exceed the image boundary ['
                                +str(column_num)+','+str(row_num)+']')
        else:
                msg.showwarning('Warning','Please select element')
    else:
        msg.showwarning('Warning','Please load result data')



def selElements():
    if resultFlag.get():
        top = tk.Toplevel()
        if selectElements.get():
            results = list(map(int,selectElements.get().split(',')))
        else:
            results=[]
        frame1 = tk.Frame(top)
        frame1.grid(row=0,column=0)
        name = locals()
        name2 = locals()
        x = 0
        y = 0
        #create elements select checkbutton group
        for i in elements_interested:
            name2['v'+str(i)] = tk.IntVar()
            if i in results:
                name2['v'+str(i)].set(1)
            name[str(All_Elements[i-1])+str(i)] = tk.Checkbutton(frame1,
                 text=str(i)+' '+str(All_Elements[i-1]),
                 variable=name2['v'+str(i)])
            name[str(All_Elements[i-1])+str(i)].grid(row=x,column=y,stick='w')
            y += 1
            if y == 10:
                x += 1
                y = 0
        #store the selected elements number
        def selElements1():
                selElementsIndex=''
                for i in elements_interested:
                    if name2['v'+str(i)].get():
                        selElementsIndex += str(i)+','
                selElementsIndex = selElementsIndex[:-1]
                selectElements.set(selElementsIndex)
                top.destroy()
        frame2 = tk.Frame(top)
        frame2.grid(row=1,column=0)
        b2 = tk.Button(frame2, text='OK',width=5,command=selElements1)
        b2.pack()
    else:
        msg.showwarning('Warning','Please load result data')
        

def confidenceSet(v):
    confidenceThreshold.set(v)

def selPixel():
    if resultFlag.get():
        top=tk.Toplevel()
        tifImage = Image.open('data/R117.tif')  
        tifImageResize = tifImage.resize((column_num,row_num))
        tk_image = ImageTk.PhotoImage(tifImageResize,master=top)   
        def selTest(event):
            temp.set(str(event.x)+', '+str(event.y))
            pixelX.set(event.x)
            pixelY.set(event.y)
        def comfirmPixel():
            top.destroy()
        tifLabel = tk.Label(top,image=tk_image,width=column_num,height=row_num)
        tifLabel.image=tk_image
        tifLabel.bind('<Button-1>',selTest)   
        tifLabel.pack(padx=5, pady=5) 
        temp=tk.StringVar()
        selPixelLabel = tk.Label(top,textvariable=temp,width=30,height=2,borderwidth=2,relief='ridge')
        selPixelLabel.pack(pady=5)
        selPixelButton = tk.Button(top,text='OK',command=comfirmPixel,width=20)
        selPixelButton.pack(pady=5)
    else:
        msg.showwarning('Warning','Please load result data')


def clearPixel():
    pixelX.set(1)
    pixelY.set(1)

def viewPixel():
    pass
    
    
#Variables 
fpath_mat = tk.StringVar()
fpath_raw = tk.StringVar()
info = tk.StringVar()
info.set('Please select result data file')
selectElements = tk.StringVar()
confidenceThreshold = tk.DoubleVar()
confidenceThreshold.set(0.0)
line = tk.IntVar()
line.set(1)
pixelX = tk.IntVar()
pixelX.set(1)
pixelY = tk.IntVar()
pixelY.set(1)
#Flag
resultFlag = tk.IntVar()
resultFlag.set(0)
XRFFlag = tk.IntVar()
XRFFlag.set(0)


#####################################################################
#frame1/load file 
frame1 = tk.Frame(root)
frame1.grid(row=0,column=0,padx=10,pady=5,ipadx=5)
#load mat file/label
fileLabel_mat = tk.Label(frame1,text='Result file name:')
fileLabel_mat.grid(row=0,column=0,sticky='e')
#load mat file/entry
filePath_mat = tk.Entry(frame1,width=60,textvariable=fpath_mat)
filePath_mat.grid(row=0,column=1)
#load mat file/button
fileOpen_mat = tk.Button(frame1,text='Select file',command=selectResult,width=20)
fileOpen_mat.grid(row=0,column=2,padx=5,sticky='w')

#load raw file/label
fileLabel_raw = tk.Label(frame1,text='XRF data name:')
fileLabel_raw.grid(row=1,column=0,sticky='e')
#load raw file/entry
filePath_raw = tk.Entry(frame1,width=60,textvariable=fpath_raw)
filePath_raw.grid(row=1,column=1)
#load raw file/button
fileOpen_raw = tk.Button(frame1,text='Select XRF data',command=selectXRF,width=20)
fileOpen_raw.grid(row=1,column=2,padx=5,sticky='w')

#####################################################################
#frame2/set parameters
frame2 = tk.Frame(root)
frame2.grid(row=1,column=0,padx=10,pady=5)

#frame21/select elements 
frame21 = tk.LabelFrame(frame2,text='Selece Elements')
frame21.grid(row=0,column=0,padx=10,pady=5)

#frame211/select elements
frame211 = tk.Frame(frame21)
frame211.grid(row=0,column=0,padx=10,pady=5,sticky='w')
#select elements/select elements label
selectElementsLabel = tk.Label(frame211, text='Select Elements:')
selectElementsLabel.grid(row=0,column=0)
#select elements/select elements entry
#selectElementsEntry = tk.Entry(frame211,textvariable=selectElements)
selectElementsEntry = tk.Label(frame211,textvariable=selectElements,height=1,width=20,borderwidth=2,relief='ridge')
selectElementsEntry.grid(row=0,column=1)
#select elements/select elements button
selectElementsButton = tk.Button(frame211,text='Elements',command=selElements,width=10)
selectElementsButton.grid(row=0,column=2,padx=5,sticky='e')

#frame212/select confidence threshold
frame212 = tk.Frame(frame21)
frame212.grid(row=1,column=0,padx=10,pady=5,sticky='w')
#select confidence threshold label
confidenceThresholdLabel = tk.Label(frame212, text='Confidence Threshold:')
confidenceThresholdLabel.grid(row=0,column=0)
#select confidence threshold entry
confidenceThresholdEntry = tk.Entry(frame212,width=8,textvariable=confidenceThreshold)
confidenceThresholdEntry.grid(row=0,column=1)
#select confidence threshold scale bar
confidenceThresholdScale = tk.Scale(frame212,from_=0,to=1,
                                    orient=tk.HORIZONTAL,length=100,
                                    resolution=0.01,command=confidenceSet,
                                    variable=confidenceThreshold)
confidenceThresholdScale.grid(row=0,column=2,padx=5)

#frame213/select lines
frame213 = tk.LabelFrame(frame21,text='Specific Lines')
frame213.grid(row=0,column=1,rowspan=2,padx=10,pady=15)
#select lines/specific lines
KLineRadiobutton = tk.Radiobutton(frame213,text='K lines',variable=line,value=1)
KLineRadiobutton.grid(row=0,column=0,sticky='w')
LLineRadiobutton = tk.Radiobutton(frame213,text='L lines',variable=line,value=5)
LLineRadiobutton.grid(row=1,column=0,sticky='w')
MlineRadiobutton = tk.Radiobutton(frame213,text='M lines',variable=line,value=3)
MlineRadiobutton.grid(row=2,column=0,sticky='w')

#####################################################################
#frame22/select pixel
frame22 = tk.LabelFrame(frame2,text='Select Pixel')
frame22.grid(row=0,column=1,rowspan=2,pady=5)
#select pixel/pixel select button
pixelSelectButton = tk.Button(frame22,text='Select Pixel',command=selPixel,width=10)
pixelSelectButton.grid(row=0,column=0,columnspan=2,padx=10,pady=5)
#select pixel/pixel X label
pixelXLabel = tk.Label(frame22, text='X:',width=2)
pixelXLabel.grid(row=1,column=0,padx=3,pady=5)
#select pixel/pixel X entry
pixelXEntry = tk.Entry(frame22,width=8,textvariable=pixelX)
pixelXEntry.grid(row=1,column=1,padx=10,pady=5)
#select pixel/pixel Y label
pixelYLabel = tk.Label(frame22, text='Y:',width=2)
pixelYLabel.grid(row=2,column=0,padx=3,pady=5)
#select pixel/pixel Y entry
pixelYEntry = tk.Entry(frame22,width=8,textvariable=pixelY)
pixelYEntry.grid(row=2,column=1,padx=3,pady=5)
#select pixel/view pixel button
#pixelViewButton = tk.Button(frame22,text='View',command=viewPixel)
#pixelViewButton.grid(row=3,column=0,sticky='e',padx=3,pady=5)
#select pixel/clear pixel button
clearPixelButton = tk.Button(frame22,text='Clear',command=clearPixel,width=6)
clearPixelButton.grid(row=3,column=0,columnspan=2,pady=5)

#####################################################################
#frame3/information window 
frame3 = tk.Frame(root)
frame3.grid(row=2,column=0,padx=10,pady=5)
#infomation window/text box
infoWindow = tk.Label(frame3,textvariable=info,height=4,width=60,borderwidth=2, relief='ridge')
infoWindow.grid(row=0,column=0,rowspan=5,padx=10)
#select elements/view maps button
viewMapsButton = tk.Button(frame3,text='View maps',command=vemFunc,width=10)
viewMapsButton.grid(row=0,column=1,padx=5,pady=5)
#infomation window/clear button
clearPathButton = tk.Button(frame3,text='Clear',command=reset,width=10)
clearPathButton.grid(row=2,column=1,padx=5,pady=5)

#####################################################################

root.mainloop()














