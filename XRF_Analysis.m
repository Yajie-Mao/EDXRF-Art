%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%MSc Individual Project
%Image Processing for Art Investigation
%Author:Yajie Mao
%Data:4-Sep-2019
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Set the default environment
clc;
clear;
close all;
addpath(genpath(pwd));
warning off; 
load('test data\Default_parameter.mat')
%%
%load raw data
file  = fopen('R117.raw','r');
column_num = 414;
row_num = 302;
channel_num = 4096;
data_cube = fread(file, [channel_num,column_num*row_num], 'uint8');
data_cube=reshape(data_cube,[channel_num,column_num,row_num]);
patch_shape=ones(1,patch_scale,patch_scale);
%spatial filter
data_patch_cube=convn(data_cube,patch_shape,'valid');
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%1. Calibration
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
channels = (0:channel_num-1)';
pixel_x = size(data_cube,2);
pixel_y = size(data_cube,3);
peak_histogram = zeros(length(channels),1);

for x = 1:pixel_x
    for y = 1:pixel_y
        %apply lowpass filter
        data_cube_rolling_average = movmean(data_cube(:,x,y),3);
        %calculate derivative
        data_diff = diff(data_cube_rolling_average);
        for i = 1:length(data_diff)-1
            if data_diff(i)>0 && data_diff(i+1)<0 && data_cube_rolling_average(i+1)>2
                peak_histogram(i+1) = peak_histogram(i+1)+ 1;
            end
        end
    end
end
%%
%find peaks of histogram to calibrate energy and channel number
[pks,locs] = findpeaks(peak_histogram,'minpeakdistance',10);
locs = locs(pks>1000)-1;
pks = pks(pks>1000);
%%
%**MANUALLY** select elements and zero point: 0 Ca Fe Mn Pb
x = [96,465,497,687,736,802,1152,1361]';
y = [0,3.69,4.012,5.895,6.492,7.059,10.549,12.611]';
%calibration coefficients
calibration_coe=polyfit(x,y,1);
corrcoef(x,y)%goodness of fitting
%plot calibration result
xi = x(1):0.1:1450;
yi = polyval(calibration_coe,xi);

%%
%Reference sigma calculation
window = (1:ectrans(0,calibration_coe,2)+100);
x = ectrans(channels(window),calibration_coe,1);
fit_coe = zeros(3,100);
%note the Guassian function variance is different from the coefficient in
%fit function¡®gaussi¡¯,c1=sigma*sqrt(2)
for i = 1:100
        y = movmean(data_patch_cube(window,unidrnd(412),unidrnd(300)),3);
        f = fit(x,y,'gauss1');
        fit_coe(:,i) = coeffvalues(f);
end
Cref = mean(fit_coe(3,:));
Eref = mean(fit_coe(2,:));
%%
save('Default_parameter.mat','All_Elements','calibration_coe','channels'...
    ,'column_num','row_num','Cref','Eref','element_table','noise_threshold')
%%
%input user interested elements
elements_interested = [13,15,16,17,18,19,20,22,23,24,25,26,27,28,29,30,...
                        33,34,35,38,45,47,48,50,51,53,56,79,80,82,83];
%
elements_interested_line = ele_interest(element_table,elements_interested,calibration_coe);

quality_map = zeros(size(data_patch_cube,2),size(data_patch_cube,3),length(elements_interested),6);
residual_map = ones(size(data_patch_cube,2),size(data_patch_cube,3),length(elements_interested),6);
overlap_map = zeros(size(data_patch_cube,2),size(data_patch_cube,3),length(elements_interested),6);

for sel_x = 1:size(data_patch_cube,2)
    for sel_y = 1:size(data_patch_cube,3)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%2. Potential peak identification
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        %lowpass spectral filter
        data_movmean = movmean(data_patch_cube(:,sel_x,sel_y),3);
        slope_th = 0.3;%slope threshold
        noise_th = 3;%noise threshold
        
        peak_potential = zeros(8,size(elements_interested_line,2));
        %8 rows represent:
        %1: element number
        %2: characteristic line:1-Ka;2-Kb;3-Ma;4-Mb;5-La;6-Lb
        %3: energy
        %4: channel
        %5: counts
        %6: regression counts
        %7: residual
        %8: overlap
        
        %peak identificaiton
        k = 1;
        for i = 1:length(elements_interested_line(3,:))
            slope_test = abs(diff(data_movmean(elements_interested_line(4,i):elements_interested_line(4,i)+2)));
            if (slope_test(1)>slope_th || slope_test(2)>slope_th)
                if data_movmean(elements_interested_line(4,i)+1)>noise_th
                    peak_potential(1:4,k) = elements_interested_line(:,i);
                    peak_potential(5,k) = data_movmean(elements_interested_line(4,i)+1);
                    k = k+1;
                end
            end
        end
        peak_potential = peak_potential(:,1:k-1);
        
        %find overlapping peak
        c = refsigma(peak_potential(4,:),Eref,Cref,calibration_coe);
        window = 3;
        sigma = c/sqrt(2);
        overlap = ones(1,size(peak_potential,2));
        group = 1;
        for k = 1:size(peak_potential,2)-1
            sigma_p = peak_potential(3,k)+window*sigma(k);
            if sigma_p>=peak_potential(3,k+1)
                overlap(k+1) = group;
            else
                sigma_n = peak_potential(3,k+1)-window*sigma(k+1);
                if sigma_n<=peak_potential(3,k)
                    overlap(k+1) = group;
                else
                    group = group+1;
                    overlap(k+1) = group;
                end
            end
        end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%3. Quality and residual calculation
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        x = ectrans(channels,calibration_coe,1);
        y = data_movmean;
        
        if ~isempty(overlap)
            for k = 1:overlap(end)
                counts = peak_potential(5,overlap==k);
                ug = peak_potential(3,overlap==k);
                %set initial fit value [A1;ug1;A2;ug2;...c,offset]
                beta0 = [reshape([counts;ug],1,length(ug)*2)';c(k);0];
                %find spectral region
                sigma_n = ug(1)-window*sigma(k);
                sigma_p = ug(end)+window*sigma(k);
                x1 = find(x==min(x(x>sigma_n)));
                x2 = find(x==max(x(x<sigma_p)));
                %non-linear fitting
                mdl = nlinfit(x(x1:x2),y(x1:x2),@modelfun,beta0);
                
                if mdl(end-1)>0  && mdl(end-1)<0.3
                    temp = reshape(mdl(1:end-2),2,(length(mdl)-2)/2);
                    Ag = temp(1,:);
                    mu = temp(2,:);
                    Ag(abs(mu-ug)>1) = 0;
                    Ag(Ag>1000) = 0;
                    Ag(Ag<-100) = 0;
                    %save quality
                    peak_potential(6,overlap==k) = abs(abs(Ag)-abs(mdl(end)));
                    %save residual
                    peak_potential(7,overlap==k) = residual(x,y,Ag,ug,mdl(end-1),mdl(end));
                else
                    peak_potential(7,overlap==k) = 1;
                end
                
                if length(Ag) == 1
                    %save overlaping
                    peak_potential(8,overlap==k) = 0;
                else
                    peak_potential(8,overlap==k) = 1;
                end
            end
            %save to datacube
            for k=1:size(peak_potential,2)
                ele = find(elements_interested==peak_potential(1,k));
                quality_map(sel_x,sel_y,ele,peak_potential(2,k)) = abs(peak_potential(6,k));
                residual_map(sel_x,sel_y,ele,peak_potential(2,k)) = peak_potential(7,k);
                overlap_map(sel_x,sel_y,ele,peak_potential(2,k)) = peak_potential(8,k);
            end
        end
    end
end
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%4. Confidence calculation
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
pixel_x = size(quality_map,1);
pixel_y = size(quality_map,2);
element_num = length(elements_interested);

confidence_map = zeros(pixel_x,pixel_y,element_num,3);
for ele = 1:size(quality_map,3)
    for shell = 1:2:5 %1-K,3-M,5-L
        map_a=squeeze(quality_map(:,:,ele,shell));
        map_a=map_a/max(max(map_a));%nomalise
        map_b=squeeze(quality_map(:,:,ele,shell+1));
        map_b=map_b/max(max(map_b));%nomalise
        %special correlation between alpha and beta map
        R=abs(corr2(map_a,map_b));
        
        fit_a = 1-squeeze(residual_map(:,:,ele,shell));
        fit_b = 1-squeeze(residual_map(:,:,ele,shell+1));
        fit_min = min(cat(3,fit_a,fit_b),[],3);
        %confidence calculation
        confidence_map(:,:,ele,(shell+1)/2) = abs(fit_a-fit_b)*R+fit_min;
        for x = 1:size(confidence_map,1)
            for y = 1:size(confidence_map,2)
                if overlap_map(x,y,ele,shell)==0 && overlap_map(x,y,ele,shell+1)==0
                    confidence_map(x,y,ele,(shell+1)/2) = max([fit_a(x,y),fit_b(x,y)]);
                elseif xor(overlap_map(x,y,ele,shell),overlap_map(x,y,ele,shell+1))
                    confidence_map(x,y,ele,(shell+1)/2) = fit_a(x,y)*overlap_map(x,y,ele,shell)+fit_b(x,y)*overlap_map(x,y,ele,shell+1);
                end
            end
        end
    end
end
%%
%save result file
save('result.mat','quality_map','residual_map','overlap_map','confidence_map','elements_interested');
%%
%simply view quality and confidence map
prompt = 'Please select element number:\n';
sel_element = input(prompt);
ele = find(elements_interested==sel_element);

prompt = 'Please select shell number (1-K,2-M,3-L):\n';
shell = input(prompt);%1-K,3-M,5-L
line = shell*2-1;
map_a=squeeze(quality_map(:,:,ele,line));
map_b=squeeze(quality_map(:,:,ele,line+1));
shell_name={'K','M','L'};
line_name={'alpha','beta'};
figure(11)
subplot(2,2,1)
imshow(map_a',[0 max(max(max(map_a))/10,1)]);
title([All_Elements{sel_element},' ',num2str(sel_element),' '...
    ,shell_name{shell},line_name{line},' quality map'])
colorbar
subplot(2,2,2)
imshow(map_b',[0 max(max(max(map_b))/10,1)]);
title([All_Elements{sel_element},' ',num2str(sel_element),' '...
    ,shell_name{shell},line_name{line+1},' quality map'])
colorbar
subplot(2,2,3)
imshow(confidence_map(:,:,ele,shell)')
% text(sel_pixel(1),sel_pixel(2),'+','Color','red','FontSize',12)
title([All_Elements{sel_element},' ',num2str(sel_element),...
    shell_name{shell},' line confidence map'])
colorbar
temp1 = map_a;
temp1(confidence_map(:,:,ele,shell)<0.7) = 0;
subplot(2,2,4)
imshow(temp1',[0 max(max(max(map_a))/10,1)]);
title([All_Elements{sel_element},' ',num2str(sel_element),' '...
    ,shell_name{shell},line_name{line},' quality map>0.7 confidence'])
colorbar



