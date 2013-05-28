import urllib.request
import os
#import cStringIO
#import Image

def encode_coords(coords):
    '''Encodes a polyline using Google's polyline algorithm
    
    See http://code.google.com/apis/maps/documentation/polylinealgorithm.html 
    for more information.
    
    :param coords: Coordinates to transform (list of tuples in order: latitude, 
    longitude).
    :type coords: list
    :returns: Google-encoded polyline string.
    :rtype: string    
    '''
    
    result = []
    
    prev_lat = 0
    prev_lng = 0
    
    for x, y in coords:        
        lat, lng = int(y * 1e5), int(x * 1e5)
        
        d_lat = _encode_value(lat - prev_lat)
        d_lng = _encode_value(lng - prev_lng)        
        
        prev_lat, prev_lng = lat, lng
        
        result.append(d_lat)
        result.append(d_lng)
    
    return ''.join(c for r in result for c in r)
    
def _split_into_chunks(value):
    while value >= 32: #2^5, while there are at least 5 bits
        
        # first & with 2^5-1, zeros out all the bits other than the first five
        # then OR with 0x20 if another bit chunk follows
        yield (value & 31) | 0x20 
        value >>= 5
    yield value
 
def _encode_value(value):
    # Step 2 & 4
    value = ~(value << 1) if value < 0 else (value << 1)
    
    # Step 5 - 8
    chunks = _split_into_chunks(value)
    
    # Step 9-10
    return (chr(chunk + 63) for chunk in chunks)

def get_coordinates_list(filename):
    
    lines = []
    f = open(filename)
    for line in iter(f):
        lines.append(line)
    f.close()
    return lines

def get_map_with_coordinates(filename, zoom=None, imgsize="500x500", imgformat="jpeg",
                          maptype="roadmap", markers=None, path=None, polyline = None) : 
    
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
    #if path != None:
     #   request += "path=color:red|weight:5%s|&" % path 
    request += "path=color:red|enc:%s&" % polyline
       
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
        pl_coords = []
        path_list = ""
        coordinates = ""
        path = os.getcwd()
        filename = "coordinates.txt"
        fullpath = path + "\\" + filename
        print(fullpath)
        lines = get_coordinates_list(fullpath)
        
        #gets the coordinates for each marker and makes a string of paths to use for path
        for line in lines:
            coordinates = line.replace("/n","").split(' ')
            formatted_coords = "%s,%s" % (coordinates[0],coordinates[1])
            pl_coords.append((float(coordinates[1]),float(coordinates[0])))
            marker_list.append("markers=size:medium|color:0xFFFF00|" + formatted_coords)
            #path_list = path_list + "|" + formatted_coords
        
        print(pl_coords)
        polyline1 = "m|vtGucnzMckl`ApllxIfoqjHd`jGsigcJtxh`A"
        polyline2 = encode_coords(pl_coords)
        
        print(polyline2)
                  
        get_map_with_coordinates("google_map_example3", imgsize=(640,640), imgformat="png", markers=marker_list, path = path_list, polyline = polyline2)