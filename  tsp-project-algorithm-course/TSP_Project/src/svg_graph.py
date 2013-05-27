"""
 svg_graph.py

 Create an SVG version of a graph, e.g.

 <?xml version="1.0" standalone="no"?>
 <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
 <!-- based on http://www.w3schools.com/svg/svg_examples.asp -->
 <svg width="100%" height="100%" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <line x1="30" y1="40" x2="80" y2="95"
	style="stroke:rgb(99,99,99);stroke-width:2"/>
  <line x1="80" y1="95" x2="200" y2="250"
	style="stroke:rgb(99,99,99);stroke-width:2"/>
  <circle cx="30" cy="40" r="5"
	  style="stroke:black;stroke-width:1;fill:red" />
  <circle cx="80" cy="95" r="5"
	  stroke="black" stroke-width="1" fill="red" />
  <circle cx="200" cy="250" r="5"
	  stroke="black" stroke-width="1" fill="red" />
  <text x="35" y="35"
	style="font-family:Verdana;font-size:12">Boston</text>
  <text x="85" y="90"
	style="font-family:Verdana;font-size:12">Chicago</text>
  <text x="205" y="245"
	style="font-family:Verdana;font-size:12">New York</text>
 </svg>

"""

svg_header = """<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="100%" height="100%" version="1.1" xmlns="http://www.w3.org/2000/svg">
"""

svg_footer = """</svg>
"""

class SvgGraph(object):
  def __init__(self, scale=1.0):
    self.scale = scale
  def write(self, xml, filename="graph"):
    """ Write the given xml to a file; default name is 'graph.svg'. """
    if not filename.endswith('.svg'):
      filename += '.svg'
    svg_file = open(filename, 'w')
    svg_file.write(xml)
    svg_file.close()
  def window_coords(self, *xy):
    return map(lambda z: self.scale * z, xy)
  def header(self):
    return svg_header
  def footer(self):
    return svg_footer
  def line(self, x1, y1, x2, y2, color='grey', width=1):
    (x1, y1, x2, y2) = self.window_coords(x1, y1, x2, y2)
    return ("""  <line x1="%f" y1="%f" x2="%f" y2="%f"\n""" + \
           """      style="stroke:%s;stroke-width:%f"/>\n""") % \
           (x1, y1, x2, y2, color, width)
  def dot(self, x, y, color='red', radius=5):
    (x, y) = self.window_coords(x, y)
    return ("""  <circle cx="%f" cy="%f" r="%f"\n""" + \
           """      style="stroke:black;stroke-width:1;fill:%s" />\n""") % \
           (x, y, radius, color)
  def text(self, string, x, y):
    (x, y) = self.window_coords(x, y)
    return ("""  <text x="%f" y="%f"\n""" + \
           """      style="font-family:Verdana;font-size:12">%s</text>\n""") % \
           (x, y, string)



