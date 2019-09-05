import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def view_maps(atomic_number_chosen,
                      confidence_threshold,
                      confidence_map,
                      elements_interested,
                      quality_map,
                      column_num,row_num,
                      All_Elements,
                      characteristic_line,
                      sel_x,sel_y):
    plt.close('all')
    view_scale_factor=10
    
    characteristic_line_name = {1:'K lines',5:'L lines',3:'M lines'}
    characteristic_line_families_show=[u'K\u03b1',u'K\u03b2',u'L\u03b1',u'L\u03b2',u'L\u03b3',u'M\u03b1']

    #Data pre-process
    confidence_index = confidence_map<confidence_threshold
    
    quality_map_temp = np.zeros(quality_map.shape)
    for i in range(3):
        temp = quality_map[:,:,:,i*2:i*2+2].copy()
        temp[confidence_index[:,:,:,i] == True]=0
        quality_map_temp[:,:,:,i*2:i*2+2] = temp.copy()
    confidence_map_temp = confidence_map.copy()
    confidence_map_temp[confidence_index == True]=0

    top=tk.Toplevel()
    top.geometry('1200x700')
    # Create a tabcontrol
    tabControl = ttk.Notebook(top)
    
    name = locals()


    #Plot map
    for n in range(len(atomic_number_chosen)):
        #creat new tap
        name['tab'+str(atomic_number_chosen[n])] = ttk.Frame(tabControl)
        tabControl.add(name['tab'+str(atomic_number_chosen[n])], text='  '
            +All_Elements[atomic_number_chosen[n]-1]+'  ')
        
        #compute elements coordinates
        ele = int(np.argwhere(elements_interested==atomic_number_chosen[n]))
        shell = int(characteristic_line/2)
        #confidence map plot
        name['f'+str(n)] = plt.figure(All_Elements[atomic_number_chosen[n]-1]+' '+str(atomic_number_chosen[n])
            +characteristic_line_name[characteristic_line],figsize=(5,6))   
        
        #alpha quality map
        name['image_q'+str(n)+'alpha'] = quality_map_temp[:,:,ele,characteristic_line-1].T
        name['a'+str(n)] = name['f'+str(n)].add_subplot(221)
        name['im_q'+str(n)+'alpha'] = name['a'+str(n)].imshow(name['image_q'+str(n)+'alpha']
            ,vmin=0,vmax=max(1,np.max(name['image_q'+str(n)+'alpha'])/view_scale_factor),cmap=plt.cm.gray)
        name['a'+str(n)].plot(sel_x-1,sel_y-1,'r+')
        name['a'+str(n)].set_title(All_Elements[atomic_number_chosen[n]-1]+' '
            +characteristic_line_families_show[characteristic_line-1]
            +' quantity map, confidence threshold='+str(confidence_threshold))
        name['a'+str(n)].set_axis_off()
        plt.colorbar(name['im_q'+str(n)+'alpha'])        

        #beta quality map
        name['image_q'+str(n)+'beta'] = quality_map_temp[:,:,ele,characteristic_line].T
        name['a'+str(n)] = name['f'+str(n)].add_subplot(222)
        name['im_q'+str(n)+'beta'] = name['a'+str(n)].imshow(name['image_q'+str(n)+'beta']
            ,vmin=0,vmax=max(1,np.max(name['image_q'+str(n)+'beta'])/view_scale_factor),cmap=plt.cm.gray)
        name['a'+str(n)].plot(sel_x-1,sel_y-1,'r+')
        name['a'+str(n)].set_title(All_Elements[atomic_number_chosen[n]-1]+' '
            +characteristic_line_families_show[characteristic_line]
            +' quantity map, confidence threshold='+str(confidence_threshold))
        name['a'+str(n)].set_axis_off()
        plt.colorbar(name['im_q'+str(n)+'beta'])        

        #confidence map
        name['image_c'+str(n)] = confidence_map_temp[:,:,ele,shell].T
        name['a'+str(n)] = name['f'+str(n)].add_subplot(223)
        name['im_c'+str(n)] = name['a'+str(n)].imshow(name['image_c'+str(n)],vmin=0, vmax=1,cmap=plt.cm.gray)
        name['a'+str(n)].plot(sel_x-1,sel_y-1,'r+')
        name['a'+str(n)].set_title(All_Elements[atomic_number_chosen[n]-1]+' '
            +characteristic_line_name[characteristic_line]
            +' confidence map, confidence threshold='+str(confidence_threshold))
        name['a'+str(n)].set_axis_off()
        plt.colorbar(name['im_c'+str(n)])
        
        #confidence histogram
        confidence_temp = confidence_map[sel_x-1,sel_y-1,:,:].squeeze()
        bar_data = np.max(confidence_temp,axis=1)
        bar_data_index = np.where(bar_data>0)
        element_index=elements_interested[bar_data_index]
        elements = [All_Elements[x-1] for x in element_index]
        bar_data = bar_data[bar_data>0]
        name['a'+str(n)] = name['f'+str(n)].add_subplot(224)
        name['im_bar'+str(n)] = name['a'+str(n)].bar(range(len(bar_data)),bar_data,tick_label=elements)
        
        name['a'+str(n)].set_title('Elements confidence at pixel ['+str(sel_x)+','+str(sel_y)+']')

        #pack canvas
        name['canvas'+str(n)] = FigureCanvasTkAgg(name['f'+str(n)], master=name['tab'+str(atomic_number_chosen[n])])
        name['canvas'+str(n)].draw()
        name['canvas'+str(n)].get_tk_widget().pack(side=tk.TOP,fill=tk.BOTH,expand=tk.YES)
        
    #pack tab    
    tabControl.pack(expand=1,fill='both')
