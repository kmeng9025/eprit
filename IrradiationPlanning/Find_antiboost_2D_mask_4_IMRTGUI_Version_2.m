function [ Bev_masks_Hypoxia ] = Find_antiboost_2D_mask_4_IMRTGUI_Version_2( Bev_masks_Hypoxia   )
%This function is in reponse to something howard requested of the IMRT_3
%project. his request is that the anti-boost is the same volume as the
%boost. This function is a response to BE suggestion that we should just do
%an anti-plan from the BEV boost mask instead of mucking about in 3D.


%Matt Maggio 5/23/2016

%changes requested from version 3 of this function: HH requested that we
%create our antiboost mask such that it fulfills 2 conditions. 
%1) Is the same area as the Hypoxic area dilated by 2 EPR voxels in
%radius 2.4mm
%2) Is does not include the area from the Hypoxic area dilated by 1 EPR
%voxel in radius 1.2mm
%I make these changes in Version 4

%Matt Maggio 8/24/2016


% outpath= 'Z:\CenterProjects\IMRT_3_development\Anti_boost_development\'
% cd(outpath);
% load('IMRT_034_A_0pnt_1_margin_Plug_production_dataset.mat')
%load('IMRT_027_0pnt_1_margin_Plug_production_dataset.mat')
% Y=[]
%Standard angle sets.
% angles = 0:360/5:360 -(360/5);
% mask_out_boost =1;
%[Bev_masks] = maskbev(angles , Tumor_CT, Tumor_CT, mask_out_boost  )
% [Bev_masks_Hypoxia] = maskbev(angles , Tumor_CT, Hypoxia_CT, mask_out_boost  )
% [Bev_masks_Tumor] = maskbev(angles , Tumor_CT, Tumor_CT, mask_out_boost  )
Scaling_factor = 2;
%Scaling_factor = 1.58;
% clc

% for ii=1:length(Bev_masks_Hypoxia);
% Boost = Bev_masks_Hypoxia.Boost_map;
Boost = Bev_masks_Hypoxia.Dilated_boost_map; 
% Boost = Bev_masks_Hypoxia.Subtract_Dilated_boost_map; 
Volume_Boost = numel(find(Boost));

Antiboost = Boost;
Volume_Antiboost = numel(find(Antiboost));
se = strel('disk',4);
se_1 = ones(3,3);

%fprintf(1,'Ratio of antiboost mask to boost mask:  ');
Antiboost_dil = Boost*0;
Loop_count = 0;

while numel(find(Antiboost_dil-Boost ==1)) < Volume_Boost
    Antiboost_dil = imdilate(Antiboost,se);
    
    Outline_dil = imdilate(Antiboost,se);
    Outline = Outline_dil & ~Antiboost;
    
    idx = find(Outline);
    %Just add a random collection of all of the voxels that would have been
    %added. Draw without replacement and make each index 1
    %Random_draw = randsample(length(idx),length(idx));
    
    if numel(find(Antiboost_dil-Boost)) >= Volume_Boost
    

    
    Antiboost(idx)=1;
 
    Volume_Antiboost = numel(find(Antiboost));    
    disp(sprintf('%s','Loop num ',num2str(Loop_count) ,' Antiboost at ',num2str(Volume_Antiboost),' voxels out of out of ' , num2str(Scaling_factor*Volume_Boost)))
    if Volume_Antiboost >= Scaling_factor*Volume_Boost
        break
    end    

    Test=1;
    
    else
    Antiboost = Antiboost_dil;
     
    Loop_count = Loop_count + 1;
    
    
    Volume_Antiboost = numel(find(Antiboost));


    end
end
    
% end
%fprintf('\n')
Antiboost(find(Boost)) =0;


    %Antiboost= Bev_masks_Hypoxia{ii}.Antiboost_map;   
% 
% se_2 = strel('disk',8)
% Antiboost_dil = imdilate(Antiboost,se_2);
% Antiboost_dil(find(Bev_masks_Hypoxia{ii}.Boost_map )) =0;    

Bev_masks_Hypoxia.Antiboost_map = Antiboost;


%save('IMRT_034_BEV_masks', 'Bev_masks_Hypoxia')
%

end

