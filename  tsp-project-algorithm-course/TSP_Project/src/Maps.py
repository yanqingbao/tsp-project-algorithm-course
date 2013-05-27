import urllib.request
import os
#import cStringIO
#import Image

def get_coordinates_list(filename):
    
    lines = []
    f = open(filename)
    for line in iter(f):
        lines.append(line)
    f.close()
    return lines

def get_map_with_coordinates(filename, zoom=None, imgsize="500x500", imgformat="jpeg",
                          maptype="roadmap", markers=None) : 
    
    #assembling the URL
    #base URL
    request = "http://maps.google.com/maps/api/staticmap?"
    
    request += "size=%ix%i&" % (imgsize)  # tuple of ints, up to 640 by 640
    request += "format=%s&" % imgformat
    request += "maptype=%s&" % maptype  # roadmap, satellite, hybrid, terrain
    
    if markers != None:
        for marker in markers:
            request += "%s&" % marker
            
    request += "sensor=false&"
           
    print(request)
    
    urllib.request.urlretrieve(request, filename+"."+imgformat)
    
    """   
    web_sock = urllib.urlopen(request)
    imgdata = cStringIO.StringIO(web_sock.read()) #StringIO to hold the image
    
    try:
        PIL_img = Image.open(imgdata)
    except IOError:
        print imgdata.read()
        
    else:
        PIL_img.show() #shows the image
    """
    
if __name__ == '__main__':
    
        marker_list = []
        path = os.getcwd()
        filename = "coordinates.txt"
        fullpath = path + "\\" + filename
        print(fullpath)
        counter = 1
        lines = get_coordinates_list(fullpath)
        print(lines)
        
        for line in lines:
            coordinates = line.split(' ')            
            marker_list.append("markers=size:tiny|label:%s|color:0xFFFF00|%s,%s|" % (counter,coordinates[0],coordinates[1]))
            counter += 1
        
        get_map_with_coordinates("google_map_example3", imgsize=(640,640), imgformat="png", markers=marker_list )
        

