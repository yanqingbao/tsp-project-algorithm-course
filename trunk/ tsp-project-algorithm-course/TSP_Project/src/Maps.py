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
                          maptype="roadmap", markers=None, path=None) : 
    
    #assembling the URL
    #base URL
    request = "http://maps.google.com/maps/api/staticmap?"
    
    request += "size=%ix%i&" % (imgsize)  # tuple of ints, up to 640 by 640
    request += "format=%s&" % imgformat
    request += "maptype=%s&" % maptype  # roadmap, satellite, hybrid, terrain
    
    #adds markers parameters to the map
    if markers != None:
        for marker in markers:
            request += "%s&" % marker
    
    #draws a path between the markers
    if path != None:
        request += "path=color:red%s|&" % path 
        
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
        path_list = ""
        path = os.getcwd()
        filename = "coordinates.txt"
        fullpath = path + "\\" + filename
        print(fullpath)
        lines = get_coordinates_list(fullpath)
        #print(lines)
        
        #gets the coordinates for each marker and makes a string of paths to use for path
        for line in lines:
            coordinates = line.replace("/n","").split(' ')
            formatted_coords = "%s, %s" % (coordinates[0],coordinates[1])
            #print(formatted_coords)
            marker_list.append("markers=size:medium|color:0xFFFF00|" + formatted_coords)
            path_list = path_list + "|" + formatted_coords
                   
        get_map_with_coordinates("google_map_example3", imgsize=(640,640), imgformat="png", markers=marker_list, path = path_list)