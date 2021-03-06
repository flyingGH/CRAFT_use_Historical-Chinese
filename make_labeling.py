import numpy as np
import cv2
import math
import os
import imgproc
import csv
import natsort
import cutting
from PIL import Image, ImageFilter
from PIL import ImageFont 
from PIL import ImageDraw 
import img_post
from operator import itemgetter
from pathlib import Path 

def make_dirs():
    output_dirnames = [ 'score', 'og_bri', 'resize', 'csv_save', 'save_rec', 'csv']
    
    outpath = Path('./output')

    if not os.path.exists(outpath):
        os.makedirs(outpath)

    for odir in output_dirnames:
        dname = outpath / odir 
        os.makedirs(dname, exist_ok=True) 

def saveLabel():
    make_dirs()

    path = './output/score/'
    path_list = os.listdir(path)
    count = len(path_list)

    resize_path = './output/og_bri/'
    resize_list = os.listdir(resize_path)

    res_path = './output/resize/'
    re_list = os.listdir(res_path)

    csv_root = './output/csv_save/' #라벨링한 CSV 파일을 저장할 경로
    save_path = './output/save_rec/' #상자 이미지를 저장할 경로
    if not os.path.isdir(csv_root):
        os.mkdir(csv_root)
    if not os.path.isdir(save_path):
        os.mkdir(save_path)


    page_num = 0 # 상자가 표시 된 이미지의 장 수

    csv_og= './output/csv/' # 오리지널 Csv 파일
    txt_list = os.listdir(csv_og) #csv 파일 경로
    cut_h = 0
    cut_w = 0

    x = natsort.natsorted
    for i in range(0, count): 
        C =[]
        poly =[]
        del C[:]
        main =[]
        del main[:]
    
        x = natsort.natsorted(path_list) #스코어 이진화 이미지
        y = natsort.natsorted(resize_list) # 원본 이진화 이미지
        z = natsort.natsorted(re_list) # 원본 이미지

        csv_srot = natsort.natsorted(txt_list) # csv 파일의 csv를 정렬
        csv_f = open(csv_og+csv_srot[i], 'r', encoding='UTF8')
        line_c = csv.reader(csv_f)

        # csv의 한줄의 데이터를 리스트c에 저장
        append_C = C.append
        for lines in line_c:
            append_C(lines)

        #글자가 있는 부분을 crop 하기 위한 부분
        #===============Crop을 위한 소팅==========================================#
        append_Poly = poly.append
        append_Main = main.append
        for k in range(0,len(C)):
            append_Poly(C[k])
            real =[int(poly[k][0]),int(poly[k][1]),int(poly[k][4]),int(poly[k][5])]
            append_Main(real)
        area = img_post.crop_size(main) # 글자가 있는 부분을 찾아서 그 위치를 저장
        #craft에서 나온 region스코어의ㅏ 위치를 읽어온다.
        #=========================================================================#

        img_score = Image.open('./output/score/'+x[i]) # 스코어 이진화 이미지
        img_og = Image.open('./output/og_bri/'+y[i]) # 원본 이진화 이미지
        img_re = Image.open('./output/resize/'+z[i]) # 원본 이미지

        # 원본 이미지도 크기에 맞게 자르기
        re_img = img_re.crop(area)  

        rw, rh = re_img.size #자른 이미지의 크기 저장
        #crop_re_img = crop_re_img.resize((rw, rh))

        if not os.path.isdir('./output/resize_img/'):
            os.makedirs('./output/resize_img/')
        re_img.save('./output/resize_img/' + z[i])
        # 원본 이미지에서 글자가 있는 부분이 corp 된 이미지 저장


        crop_re_img = img_og.crop(area)  #원본 이미지에서 글자가 있는 부분을 크롭
        rw, rh = crop_re_img.size
        crop_re_img = np.array(crop_re_img)
        crop_re_img = img_post.del_line_H_CV2(rh, rw, crop_re_img) # 합성 이미지에서 
        ret, crop_re_img = cv2.threshold(crop_re_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        #스코어 이미지
        crop_score_img = img_score.crop(area) 
        rw, rh = crop_score_img.size
        crop_score_img = np.array(crop_score_img)
        ret, crop_score_img = cv2.threshold(crop_score_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 이미지 합성
        addImg = cv2.add(crop_score_img, crop_re_img) # 원본 이미지와 스코어 이미지 합성
        cv2.imwrite('./output/post2/save_'+str(page_num)+'.jpg', addImg) # 합성 이미지 저장 

        # 라벨링 한 이미지 상자 그려줄 이미지 로드
        crop_re_img = cv2.imread('./output/resize_img/'+z[i], cv2.IMREAD_COLOR)

        # 커넥티드 컴포넌트 라벨링 진행
        nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(addImg,connectivity=8)

        csv_list = os.listdir('./output/csv/')
        c = natsort.natsorted(csv_list)

        res_file_csv = csv_root + c[i]
        csvfile = open(res_file_csv,'w',newline='')
        
        csvwriter = csv.writer(csvfile)

        # 레이블링 박스의 크기 판별 

        if int(rw/15) < cut_w and cut_w != 0:
            cut_w = cut_w
            cut_h = cut_h
        else:
            cut_h = int(rh/18)
            cut_w = int(rw/15) 

        # 레이블링한 것 중 일정 크기의 이미지만 지정 하여 번호 부여 
        for i in range(1, nlabels):
            
            size = stats[i, cv2.CC_STAT_AREA]

            if size < 300: continue
            elif size > 20000: continue
            #일정 사이즈는 넘기고 진행 

            x, y = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
            w, h = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            
            if h > cut_h: continue
            if h < int(cut_h/5): continue
            if w > cut_w: continue
            if w < int(cut_w/2): continue

            crop_re_img = cv2.rectangle(crop_re_img, (x, y), (x + w, y + h),(0, 0, 255), 1)
            k = x, y, x+w, y+h #상자 좌표를 csv파일에 저장
            
            csvwriter.writerow(k) # 각 글자의 좌측상단 우측하단의 좌표값을 저장 
            
        
        cv2.imwrite(save_path+'save_'+str(page_num)+'.jpg', crop_re_img) #박스가 쳐진 이미지를 저장
        print(save_path+'save_'+str(page_num)+'.jpg')
        page_num =page_num+1
    