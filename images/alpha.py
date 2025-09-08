import cv2
while True:
    img_name=input()
    img=cv2.imread(img_name,flags=cv2.IMREAD_UNCHANGED)
    b,g,r,a=cv2.split(img)
    a[:,:]=a[:,:]*float(input())
    img=cv2.merge([b,g,r,a])
    cv2.imwrite(img_name,img)
