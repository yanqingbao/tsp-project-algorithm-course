"""
 tsp.py
 
 Looking at the traveling salesman problem (TSP)
 and the Lin-Kernighan algorithm for interative improvement.

 The ideas here are taken primarily from Johnson and McGeoch's 1995 
   http://www.research.att.com/~dsj/papers/TSPchapter.pdf, pg 39-42.
 which describes the original Lin-Kernighan(1973) approach
 as well as their modifications.

 Tested with python 2.6.1.
  
 Jim Mahoney | Marlboro College | GPL

 history
   Nov 2010 - working version while Richard Scrugs was around.
   Apr 2011 - profiling etc for algorithms course
 
"""

import re
import time
import math
import random
import doctest
from svg_graph import SvgGraph

class memoized(object):
  # from http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize  
  """Decorator that caches a function's return value each time it is called.
     If called later with the same arguments, the cached value is returned, and
     not re-evaluated.
  """
  def __init__(self, func):
    self.func = func
    self.cache = {}
  def __call__(self, *args):
    try:
      return self.cache[args]
    except KeyError:
      value = self.func(*args)
      self.cache[args] = value
      return value
    except TypeError:
      # uncachable -- for instance, passing a list as an argument.
      # Better to not cache than to blow up entirely.
      return self.func(*args)
  def __repr__(self):
    """Return the function's docstring."""
    return self.func.__doc__
  def __get__(self, obj, objtype):
    """Support instance methods."""
    return functools.partial(self.__call__, obj)

@memoized
def factorial(n):
  """ Return n!
      >>> factorial(0)
      1
      >>> factorial(5)
      120
  """
  # Quick and easy for light duty use; python's default recursion limit is 1000.
  # And if performance matters, this should be memoized;
  # see http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize .
  if n <= 1:
    return 1
  else:
    return n * factorial(n-1)

def permutations(collection):
  """ Generate all permutations of collection[] recursively.
      From http://snippets.dzone.com/posts/show/753
      >>> list(permutations("abc"))
      ['abc', 'bac', 'bca', 'acb', 'cab', 'cba']
  """
  if len(collection) <= 1:
    yield collection
  else:
    for permutation in permutations(collection[1:]):
      for i in range(len(permutation)+1):
        yield permutation[:i] + collection[0:1] + permutation[i:]

def proper_permutations(collection):
  """ Generate the subset of permutations of collection[]
      without cyclic or reverse variants. To do this, we fix
      the 0th element of the subset and require that 1st < 2nd.
      This corresponds to the different traveling salesman paths,
      since a given path can be started at any city and traversed
      in either direction.
      >>> list(proper_permutations("abcd"))
      ['abcd', 'acdb', 'abdc']
  """
  for permutation in permutations(collection[1:]):
    if permutation[0] < permutation[1]:
      yield collection[0:1] + permutation


class City(object):
  """ A node in a TSP graph.

      >>> boston = City('Boston', 1.0, 1.0)
      >>> str(boston)
      'Boston (1.00, 1.00)'
      >>> boston < City('New York', 0.0, 0.0)
      True
      >>> random_city = City()
      >>> 0 <= random_city.x <= City._grid_width
      True
      >>> random_city.name[0] == '#'
      True

      Don't modify a city's (name,x,y);
      it's hash, id, and string are set when created.
  """

  _count = 0
  _grid_width = 100.0    # (x,y) random coords are 0 to this

  def __init__(self, name=None, x=None, y=None):
    City._count += 1
    if x == None:
      self.x = self.random_coord()
    else:
      self.x = x
    if y == None:
      self.y = self.random_coord()
    else:
      self.y = y
    self.name = name or ('#' + str(City._count))
    self.tsp = None       # Initialized within TSP.init()
    self.roads = Roads()  #  ditto
    # This string representation is set only once.
    self._str = "%s (%4.2f, %4.2f)" % (self.name, self.x, self.y)
    self._id = id(self._str)

  def random_coord(self):
    return City._grid_width * random.random()

  def __str__(self):
    return self._str

  def __hash__(self):
    # Set hash equivalence to depend on the string representation,
    # not the default object id.
    return self._id

  def __cmp__(self, other):
    return cmp(self._str, str(other))


class Listy(list):
  """ A custom list - basically in case I want more features later.
      >>> str(Listy([10,20,30]))
      '<Listy (3): 10, 20, 30>'
  """
  def __init__(self, *args):
    super(Listy, self).__init__(*args)
    try:
      # i.e. extract 'Listy' from '<class tsp_jim.Listy'>
      self._class = re.search("\.(.*)'", str(self.__class__)).group(1)
    except:
      self._class = '?'

  def __str__(self):
    if len(self) <= 4:
      return "<%s (%i): %s>" % \
             (self._class, len(self), ", ".join(map(str,self)))
    else:
      return "<%s (%i): %s>" % (self._class, len(self),
                                str(self[0]) + ", " + str(self[1])+ \
                                ", ..., " + \
                                str(self[-2]) + ", " + str(self[-1]))


class Road(Listy):
  """ An edge in a TSP graph connecting two Cities.         #          r3
      Don't modify its cities after it's created.           #     D -------C
      >>> (a, b) = (City('A', 0, 2), City('B', 0, 3))       #  r2 |/ 
      >>> (c, d) = (City('C', 1, 50), City('D', 0, 1))      #     A--B
      >>> (r1, r2, r3) = (Road(a,b), Road(d, a), Road(a, c))#      r1
      >>> map(str, [r1, r2, r3])
      ['A--B (1.00)', 'A--D (1.00)', 'A--C (48.01)']
      >>> r1 < r2 < r3
      True
      >>> str(r1.other(a))  # r1 city at the other end from A
      'B (0.00, 3.00)'
  """
  # I'm storing these in (road[0], road[1]) sorted alphabetically,
  # but intend to treat it as the same road in either direction.

  def __init__(self, city1, city2):
    super(Road, self).__init__(sorted([city1, city2]))
    self.length = math.sqrt((city1.x - city2.x)**2 + (city1.y - city2.y)**2)
    self._str = "%s--%s (%4.2f)" % (self[0].name, self[1].name, self.length)
    self._id = id(self._str)
    self._cmp = (self.length, self._str)
    self._other = {self[0]:self[1], self[1]:self[0]}

  def other(self, city):
    """ Return city at other end of road. """
    return self._other[city]

  def __str__(self):
    return self._str

  def __hash__(self):
    # Set these as OK as use dictionary keys and set elements.
    # Otherwise, python is unhappy about using 'em that way,
    # since they inherit from mutable lists.
    return id(self._id)

  # And since this inherits from list, it already has <, >, etc.
  # This unfortunately means that just defining __cmp__ won't work,
  # since the others take precedence.  Python calls these "rich comparisons";
  # see http://docs.python.org/library/functools.html#functools.total_ordering
  # and http://docs.python.org/reference/datamodel.html#object.__lt__ .

  def __eq__(self, other):
    return self._str == str(other)

  # The following comparisons will fail when comparing a Road with non-Road.
  # So don't do that.

  def __lt__(self, other):
    return self._cmp < other._cmp

  def __le__(self, other):
    return self._cmp <= other._cmp

  def __gt__(self, other):
    return self._cmp > other._cmp

  def __ge__(self, other):
    return self._cmp <= other._cmp


class Cities(Listy):
  """ A collection of cities with 
        * access by name
        * generation of a test case
        * cities.append(city) is implemented;
          other modifications won't preserver access by name
      >>> test6 = Cities(create='test6')
      >>> str(test6)
      '<Cities (6): A, B, ..., E, F>'
      >>> str(test6.by_name['A'])
      'A (1.00, 1.00)'
      >>> randoms = Cities(create='random', N=10)
      >>> len(randoms)
      10
  """

  # Using the window xy convention with (0,0) at top left,
  # the test6 city's layout looks like this :
  #      |
  #  1.0 |   A      B       C
  #      |
  #  2.5 |   F     E      D
  #      |
  #      +----------------------
  #          1     2      3
  def __init__(self, cities=None, create=None, N=0):
    if cities:
      assert isinstance(cities[0], City), 'Non City passed to Cities()'
    else:
      cities = []
    super(Cities, self).__init__(cities)
    self.by_name = {}
    if (create == 'random') and (N>0):
      for i in range(N):
        self.append(City())
    elif create == 'test6':
      for data in (('A', 1.0,  1.0),
                   ('B', 2.12, 1.0),
                   ('C', 3.25, 1.0),
                   ('D', 3.1,  2.5),
                   ('E', 2.1,  2.5),
                   ('F', 1.2,  2.5)):
        self.append(City(*data))

  def get(self, name):
    """ Return the city with the given name. """
    return self.by_name[name]

  def append(self, city):
    super(Cities, self).append(city)
    self.by_name[city.name] = city

  def __str__(self):
    if len(self) <= 4:
      return "<%s (%i): %s>" % (self._class, len(self),
                                ", ".join(map(lambda x: x.name, self)))
    else:
      return "<%s (%i): %s>" % (self._class, len(self),
                                self[0].name + ", " + self[1].name + \
                                ", ..., " + \
                                self[-2].name + ", " + self[-1].name)


class Roads(set):
  """ A collection of roads with
        * no duplicates
        * no city sequence
        * access by city pairs
        * access to other city from a given one
        * modifications via roads.add(road), roads.remove(road)
        * optional ordering by road length
      This is designed to be both
        * a data structure for all the roads in a TSP,
        * a base class for the Tour object used in the LK algorithm.
  """
  def __init__(self, roads=None):
    if not roads:
      roads = []
    super(Roads, self).__init__(roads)
    self.by_cities = {}
    self.by_names = {}
    self.other = {}
    self.by_length = None
    for road in self:
      self.update_cities(road)

  def update_cities(self, road):
    """  Update the by_cities and by_names dictionary with this road. """
    if road == None or self.by_cities == None:
		print " NONE FOUND"
		print " self = '%s'" % repr(self)
		print " by_cities = '%s'" % repr(self.by_cities)
		print " road = '%s'" % repr(road)
    self.by_cities[(road[0], road[1])] = road
    self.by_cities[(road[1], road[0])] = road
    self.by_names[(road[1].name, road[0].name)] = road
    self.by_names[(road[0].name, road[1].name)] = road    

  def update_by_length(self):
    """ If not yet created or invalid after modification,
        create a Listy version of the roads sorted by length,
        and store it in self.by_length.
    """
    if not self.by_length:
      self.by_length = Listy(self)
      self.by_length.sort()
      self.by_length._class = 'Roads'

  def add(self, road):
    """ Add a road to this collection. """
    super(Roads, self).add(road)
    self.update_cities(road)
    self.by_length = None

  def remove(self, road):
    """ Remove a road from this collection. """
    super(Roads, self).remove(road)
    del self.by_cities[(road[0], road[1])]
    del self.by_cities[(road[1], road[0])]
    del self.by_names[(road[0].name, road[1].name)]
    del self.by_names[(road[1].name, road[0].name)]
    self.by_length = None    

  def get(self, city1, city2):
    """ Return the road with the given city endpoints or names. """
    if isinstance(city1, City) and isinstance(city2, City):
      return self.by_cities.get((city1, city2), None)
    elif isinstance(city1, str) and isinstance(city2, str):
      return self.by_names.get((city1, city2), None)
    else:
      raise Exception('illegal argument to Roads.get')

  def __str__(self):
    """ as string version is sorted by length and city names """
    self.update_by_length()
    return str(self.by_length)


class Tour(Roads):
  """ A connected directed graph of roads (edges) and cities (vertices).

      It can be in one of two states :
        1. A closed loop, with n_cities==n_roads (i.e. a TSP tour)
           When first created, its put into this state and prints as <Tour ...>
        2. A path with a first and last city, as used in the L.K. algorithm.
           Removing a road with tour2path(road) converts to this state,
           which prints as <Path ...>.  In this state, the .modify() and
           .unmodify() methods implement the LK changes to the graph,
           while .revert() or .close() turn it back into a tour by
           either throwing away or keeping the LK modifications.
      
      >>> tour = Tour(TSP(cities='test6'), ('A', 'D', 'C', 'E', 'B', 'F'))
      >>> str(tour)
      '<Tour (6 roads, length 10.75): A - D - C - E - B - F - A>'

      >>> road_AF = tour.get('A', 'F'); str(road_AF)
      'A--F (1.51)'

      >>> tour.tour2path(road_AF, backward=True); str(tour)
      '<Path (5 roads, length 9.24, tour 10.75): F - B - E - C - D - A>'

      >>> for (city, roadAdd, roadRemove) in tour.find_lk_mods():
      ...   print "insert %s , add %s, remove %s, delta=%f" % \
                  (city.name, str(roadAdd), str(roadRemove), \
                  roadAdd.length - roadRemove.length)
      insert B , add A--B (1.12), remove B--E (1.50), delta=-0.380133
      insert F , add A--F (1.51), remove B--F (1.76), delta=-0.246384
      insert E , add A--E (1.86), remove C--E (1.89), delta=-0.029998

      >>> tour.revert(); tour.is_tour()
      True
      >>> tour.tour2path(road_AF); str(tour)     # remove A--F road
      '<Path (5 roads, length 9.24, tour 10.75): A - D - C - E - B - F>'
      >>> mods = tour.find_lk_mods()
      >>> for (city, roadAdd, roadRemove) in mods:
      ...   print "insert %s , add %s, remove %s, delta=%f" % \
                  (city.name, str(roadAdd), str(roadRemove), \
                  roadAdd.length - roadRemove.length)
      insert E , add E--F (0.90), remove B--E (1.50), delta=-0.600133
      insert A , add A--F (1.51), remove A--D (2.58), delta=-1.067423

      # Since the LK algorithm fixes one end and manipulates the other,
      # flipping the path end-for-end gives different possible changes.

      # This modification finds a better path, and a better tour.
      >>> tour.modify(*mods[0]); str(tour)    # break E-B, add E-F :
      '<Path (5 roads, length 8.64, tour 9.76): A - D - C - E - F - B>'
      >>> tour.unmodify(*mods[0]); str(tour)  # undo
      '<Path (5 roads, length 9.24, tour 10.75): A - D - C - E - B - F>'

      # This one improves the path without improving the tour.
      # (In fact, it's the same tour, though LK proceeds differently.)
      >>> tour.modify(*mods[1]); str(tour)    # edge case: break A-D, add F-A :
      '<Path (5 roads, length 8.17, tour 10.75): A - F - B - E - C - D>'
      >>> tour.unmodify(*mods[1]); str(tour)  # undo
      '<Path (5 roads, length 9.24, tour 10.75): A - D - C - E - B - F>'
      
  """
  # This is the heart of the data structure for the Lin-Kernighan algorithm.
  #
  # A path for the LK algorithm is a sequence of cities from 1 to N :
  #
  #   1 =>  2  => ... (i-1) => i => (i+1) ... (N-1) => N
  #
  # The path length is the sum of the (N-1) roads.  (The corresponding
  # tour distance is found by incrementing tha path length by
  # the length of the road from N to back to 1.)
  #
  # The LK algorithm works at the right end of this path, leaving
  # city 1 alone.  The idea is remove a road between some
  # city i and i+1, and then restore connectivity by connecting i to N.
  # The situation then looks like this :
  #
  #                            ----------------------------------
  #                            |                                |
  #   1 =>  2  => ... (i-1) => i    (i+1) => (i+2) ... (N-1) => N 
  #
  # Then the directionality of the links from (i+1) to N is flipped
  # and the cities renumbered to get this :
  #
  #                            ---------------------------------
  #                            |                               |
  #   1 =>  2  => ... (i-1) => i     N   <= (N-1) ... (i+2) <= (i+1)
  #
  # In this implementation they don't actually have numbers;
  # instead the ordering is contained in a doubly linked list
  # using a dictionary.
  #
  #   self.first = city 1
  #   self.last = city N
  #   self.neighbors[city[i]] = (city[i-1], city[i+1])
  #
  # So to do one of these LK modifications, self.last is changed
  # and self.neighbors is modified from city i onwards.
  #
  # The Road objects don't store a direction; they just contain
  # distances, and allow for sorting by length in their Roads container.
  #
  # The rest of the L.K. algorithm is just keeping track
  # of which cities/roads are good candidates for this
  # exchange : ones that weren't in the previous tour,
  # wich make the path shorter, and (optionally) which are
  # within the M'th shortest (e.g. the shortest 5) from a city.
  #
  # I'm not at all sure that this is the best way
  # to implement all this, but it should be good enough.
  #

  def __init__(self, tsp, tour):
    """ Inputs: tsp   = a TSP() instance, with cities and roads in place.
                tour  = 'default'     => tsp.cities, in their default order
                        'random'      => tsp.cities, in a random order
                        [city1, city2, ...] => that sequence of cities
                        [name1, name2, ...] => tsp.cities with these names
    """
    #
    # Initialized as a closed path from a sequence of cities
    #    closed loop iff len(self) == len(self.cities)
    #    self.neighbors[city[i]] = (city[i-1], city[i+1]) defines the sequence
    #    self.tsp.roads.get(cityX, cityY) = the road between any two cities
    #    city.roads.by_length = sorted list of all tsp roads for given city
    #
    self._str_alphaorder = False         # if true, normalize print city order
    if isinstance(tour, str):
      cities = tsp.cities                # 'default'
      if tour == 'random':
        random.shuffle(cities)           # 'random'
    elif isinstance(tour[0], City):      # [city1, city2, ...]
      cities = Cities(tour)         
    elif isinstance(tour[0], str):       # [name1, name2, ...]
      cities = Cities(map(lambda x: tsp.cities.by_name[x], tour))
    else:
      raise Exception('Illegal tour argument in Tour initialization')
    self.tsp = tsp
    self.cities = cities
    self.max_search_roads = tsp.lk_search_roads_per_city
    n = len(cities)
    roads = [tsp.roads.get(self.cities[i], self.cities[(i+1) % n]) for i in range(n)]
    super(Tour, self).__init__(roads)
    self.first = self.last = None
    self.neighbors = {}
    for i in range(n):
      self.neighbors[cities[i]] = (cities[i-1], cities[(i+1)%n])
    self.length = sum([road.length for road in self])

  def revert(self):
    """ Reset back to the original closed tour. """
    # The sequence of cities in self.cities isn't modified
    # during the LK modifications.
    self.__init__(self.tsp, self.cities)

  def close(self):
    """ Convert from an open path to a closed tour,
        keeping the city sequence generated from the LK modifications. """
    self.__init__(self.tsp, self.city_sequence())

  def find_lk_mods(self, added=None, deleted=None):
    """ Return viable L.K. modifications as described in the ascii art above,
        stored as a list of (city_insert, road_to_add, road_to_delete), where
          1. road_to_add is city N to city i
               optional speedup: only look at M=5 or so shortest from city N
          2. city_insert is city i, (2 <= i <= N-2) of the N cities.
               not city N (can't go to itself);
               not city N-1 (already in path);
          3. road_to_delete is city i to city i+1
               since there are only two roads from city in the path,
               and deleting i-1 to i leaves two disconnected paths
          4. road_to_add.length < road_to_delete, i.e. path improvement
          5. road_to_delete is not in added
               i.e. don't backtrack within one L.K. K-Opt iteration
          6. road_to_add is not in 'deleted'  (in some versions of L.K.)
        There are at most N-2 of these (or at most M=5 if using that speedup),
        and likely much fewer.
    """
    if not added:
      added = set()
    if not deleted:
      deleted = set()
    mods = []
    cityN = self.last
    # Of roads from cityN, look at the at shortest, most likely roads first.
    for road_add in cityN.roads.by_length[:self.max_search_roads]:         # 1
      city_insert = road_add.other(cityN)
      if city_insert == self.prev_city(cityN): continue                    # 2
      road_delete = self.get(city_insert, self.next_city(city_insert))     # 3
      if road_add.length >= road_delete.length: continue                   # 4
      if road_delete in added: continue                                    # 5
      if road_add in deleted: continue                                     # 6
      mods.append((city_insert, road_add, road_delete))
    return mods
    
  def tour_length(self):
    """ Return the length of this tour or (if we're in the Path state)
        the corresponding closed TSP tour. """
    if self.is_tour():
      return self.length
    else:
      return self.length + self.tsp.roads.get(self.first, self.last).length

  def is_forward(self, road):
    """ Return True if road[0] => road[1] is along the path,
        or if it will be once its filled in. """
    # So either road[0] => road[1]   i.e. next(0) = 1
    # or road[-1] => road[0] = None / gap / None => road[1] => road[2] .
    return self.next_city(road[0]) == road[1] or \
           self.next_city(road[0]) == None == self.prev_city(road[1])

  def is_tour(self):
    """ Return true if in original, Tour state,
        as opposed to the LK Path state. """
    # return len(self) == len(self.cities)       # i.e. n_roads == n_cities
    return not self.first and not self.last  # This should work, too.

  def tour2path(self, road, backward=False):
    """ Convert a closed tour into an LK path by removing a road.
        If backward is true, also flip the direction of the path. """
    assert self.is_tour()
    if backward:
      self.flip_direction()
    if self.is_forward(road):
      (self.first, self.last) = (road[1], road[0])
    else:
      (self.first, self.last) = (road[0], road[1])
    self.remove(road)

  def replace_neighbors(self, road, (a, b)):
    """ Replace neighbors of road ends with new neighbors (a,b) """
    (before0, after0) = self.neighbors[road[0]]
    (before1, after1) = self.neighbors[road[1]]
    if self.is_forward(road):
      self.neighbors[road[0]] = (before0, b)
      self.neighbors[road[1]] = (a, after1)
    else:
      self.neighbors[road[1]] = (before1, a)
      self.neighbors[road[0]] = (b, after0)

  def add(self, road):
    """ Add a road. """
    super(Tour, self).add(road)
    self.length += road.length
    self.replace_neighbors(road, road)

  def remove(self, road):
    """ Remove a road. """
    super(Tour, self).remove(road)
    self.length -= road.length
    self.replace_neighbors(road, (None, None))

  def flip1city(self, city):
    """ Change directionality of neighbors of a city. """
    (before, after) = self.neighbors[city]
    self.neighbors[city] = (after, before)
    
  def flip_direction(self, cityA=None, cityB=None):
    if cityA:
      city = cityA
      while city:
        next_city = self.next_city(city)
        self.flip1city(city)
        if city == cityB:
          break
        city = next_city
    else:
      for city in self.cities:
        self.flip1city(city)
      (self.first, self.last) = (self.last, self.first)

  def modify(self, city_insert, road_add, road_delete):
    """ Do LK path modification """
    # These arguments aren't independent;
    # road_add and road_delete can both be determined from city_insert.
    # but since I need all three of 'em in find_lk_mods and here,
    # it seems simplest to just pass all of 'em around.
    #
    # Here's the picture of what's going on, copied from up above.
    #                            ----------------------------------
    #                            |                                |
    #   1 =>  2  => ... (i-1) => i    (i+1) => (i+2) ... (N-1) => N 
    #
    #   city_insert  is  city[i]
    #   self.last    is  city[N]
    #   road_add     is  city[N] => city[i] (over the top); 
    #   road_delete  is  city[i] => i+1
    #
    iPlus1 = road_delete.other(city_insert)
    cityN = self.last
    if not road_delete in self:
      raise Exception("Oops - tried to remove %s from %s" % \
                      (str(road_delete), ",".join(map(str,self))))
    self.remove(road_delete)
    self.flip_direction(iPlus1, cityN)
    self.add(road_add)
    self.last = iPlus1

  def unmodify(self, city_insert, road_add, road_delete):
    """ Undo LK path modification """
    # See the picture above; I'm using the original numbering scheme.
    iPlus1 = self.last
    cityN = road_add.other(city_insert)
    if not road_add in self:
      raise Exception("Oops - tried to remove %s from set %s" % \
                      (str(road_add), ",".join(map(str,self))))
    self.remove(road_add)
    self.flip_direction(cityN, iPlus1)
    self.add(road_delete)
    self.last = cityN

  def next_city(self, city):
    return self.neighbors[city][1]

  def prev_city(self, city):
    return self.neighbors[city][0]

  def city_sequence(self, alphaorder=False):
    """ Return the cities along the path from first to last,
        or the cities in the tour.

        If alphaorder and is a tour, return the alphabetically lowest
        city name first, and of the two possible directions from
        there, choose the lowest alpha city.

        >>> t = Tour(TSP(cities='test6'), ('D', 'C', 'E', 'F', 'B', 'A'))
        >>> t._str_alphaorder = False
        >>> str(t)
        '<Tour (6 roads, length 9.76): D - C - E - F - B - A - D>'
        >>> t._str_alphaorder = True
        >>> str(t)
        '<Tour (6 roads, length 9.76): A - B - F - E - C - D - A>'
        """
    if not self.first and not self.last:
      cities =  self.cities
    else:
      cities = Cities()
      city = self.first
      while True:
        cities.append(city)
        if city == self.last:
          break
        city = self.next_city(city)
    if alphaorder and self.is_tour():
      city_first = min(map(lambda x: (x.name, x), cities))[1]
      index_first = cities.index(city_first)
      cities = cities[index_first:] + cities[:index_first]
      if cities[1].name > cities[-1].name:
        cities[1:] = list(reversed(cities[1:]))
    return cities

  def __str__(self):
    city_sequence = self.city_sequence(self._str_alphaorder)
    names = [c.name for c in city_sequence]
    if len(names) > 8:
      names[3:-3] = ['...']
    city_string = " - ".join(names)
    if len(self.cities) == len(self):
      city_string += " - " + city_sequence[0].name
      return "<Tour (%i roads, length %4.2f): %s>" % \
             (len(self), self.length, city_string)
    else:
      return "<Path (%i roads, length %4.2f, tour %4.2f): %s>" % \
             (len(self), self.length, self.tour_length(), city_string)


class RestartLK(Exception):
  """ A generic custom exception """
  pass


class TSP(object):
  """ An instance of the traveling salesman problem.
  
      >>> tsp = TSP(cities='test6', tour=('A', 'D', 'C', 'E', 'B', 'F'))
      >>> print(tsp)
      <TSP:
        <Cities (6): A, B, ..., E, F>
        <Roads (15): E--F (0.90), D--E (1.00), ..., C--F (2.54), A--D (2.58)>
        <Tour (6 roads, length 10.75): A - D - C - E - B - F - A> >

      >>> tsp.print_brute_force() 
      -- brute force analysis of 6 cities with 60 distinct tours --
      best is <Tour (6 roads, length 7.17): A - B - C - D - E - F - A>
      worst is <Tour (6 roads, length 11.88): A - C - E - B - F - D - A>
      
      >>> tsp.lk_verbose = False
      >>> str(tsp.tour)
      '<Tour (6 roads, length 10.75): A - D - C - E - B - F - A>'
      >>> tsp.LK()
      >>> "%.2f" % tsp.tour.length
      '7.17'

      >>> randomTSP = TSP(cities=10, tour='random')
      >>> len(randomTSP.tour)
      10
  """

  #    The LK search wasn't behaving deterministically:
  #    small changes in the code gave ordering variations in the best path.
  #    Within the same program, repeated 
  #       tsp = TSP(cities='test6', tour=('A', 'D', 'C', 'E', 'B', 'F'))
  #       tsp.LK()
  #       str(tsp.tour)
  #    gave variations like
  #     '<Tour (6 roads, length 7.17): D - C - B - A - F - E - D>'
  #     '<Tour (6 roads, length 7.17): D - E - F - A - B - C - D>'
  #     '<Tour (6 roads, length 7.17): A - F - E - D - C - B - A> >
  #    Might be a loop over a set or dict (with undefined traversal order).
  #    Now the tour is made "proper" (one chosen of these equivalent
  #    versions); and I'm not sure if this is still true.
  #    And it may not matter anway ... just didn't understand it.

  def __init__(self, cities=None, tour=None):
    """ Inputs:
            cities = None | [city1, city2, ...] | 'test6'
            tour = None | 'random' | 'default' | [city1, ..] | ['name1', ..]
    """

    # ---- Lin-Kernighan search parameters ----
    self.lk_verbose               = False
    self.lk_depth_limit           = None   # None => until no candidates
    self.lk_restart_better_tours  = True   # i.e. Johnson; False in LK paper
    self.lk_search_roads_per_city = 10     # -1 => all; 5 in LK paper
    # Other possible parameters: 
    #   (L.K. paper uses both of these following constraints;
    #    Johnson uses only the first (constrain_added).
    #    These options would change #4 and #5 in Path.find_lk_mods() )
    # self.lk_constrain_added   = True  #  road_to_delete not in added
    # self.lk_constrain_deleted =True   #  road_to_add not in deleted

    if type(cities)==int:
      self.cities = Cities(create='random', N=cities)
    elif cities == 'test6':
      self.cities = Cities(create='test6')
    elif cities:
      self.cities = Cities(cities)
    else:
      self.cities = Cities()
    self.init_TSP()
    if tour:
      self.tour = Tour(self, tour)
    else:
      self.tour = None

  def tour_length(self):
    """ Return length of tour. """
    return self.tour.tour_length()

  def __str__(self):
    result = "<TSP:\n  " + str(self.cities) + "\n  " + str(self.roads)
    if self.tour:
      result += "\n  " + str(self.tour)
    return result + " >"

  def randomize_tour(self):
    """ reorder current cities into a random tour """
    self.tour = Tour(self, 'random')

  def graph(self, filename=None, all_lines=True, scale=100.0):
    """ Return SVG graph string of TSP.
        If filename is given, force it to end in '.svg'
        and output the SVG graph to it.
        scale is a size multiplier, converting (x,y) to pixels.
    """
    svg = SvgGraph(scale=scale)
    xml = svg.header()
    if all_lines :
      for road in self.roads:
        xml += svg.line(road[0].x, road[0].y, road[1].x, road[1].y)
    if self.tour:
      for road in self.tour:
        xml += svg.line(road[0].x, road[0].y, road[1].x, road[1].y,
                        color='blue', width=3)
    for city in self.cities:
      xml += svg.dot(city.x, city.y)
      xml += svg.text(city.name, city.x+0.05, city.y-0.05)
    xml += svg.footer()
    if filename:
      svg.write(xml, filename)
    return xml

  def print_brute_force(self):
    """ analyze and print all tours with full search over permutations """
    #
    # There are (N-1)!/2 closed tours of N cities; with N=6 this is 60.
    # For the test6 case this analysis gives :
    #   best is ['A', 'B', 'C', 'D', 'E', 'F'] with length = 7.1708
    #   worst is ['A', 'C', 'E', 'B', 'F', 'D'] with length = 11.8806
    #
    cities = self.cities
    print "-- brute force analysis of %i cities with %i distinct tours --" \
          % (len(cities), factorial(len(cities)-1)/2)
    names = map(lambda x: x.name, cities)

    ## before profile - this way of doing this was > 20% slower
    #lengths_perms = [(Tour(self, p).tour_length(), Tour(self, p))
    #                 for p in proper_permutations(names)]

    ## after profile - only call Tour() once.
    perms = proper_permutations(names)
    lengths_perms = []
    for p in perms:
      t = Tour(self, p)
      lengths_perms.append((t.tour_length(), t))

    best = min(lengths_perms)
    worst = max(lengths_perms)
    best[1]._str_alphaorder = worst[1]._str_alphaorder = True
    #print "best is %s with length = %6.4f" % (str(best[1]), best[0])
    #print "worst is %s with length = %6.4f" % (str(worst[1]), worst[0])
    print "best is %s" % str(best[1])
    print "worst is %s" % str(worst[1])

  def init_TSP(self):
    """ Starting with self.cities,
        this sets up the various TSP internals and links between 'em :
        0. Create self.roads.
        1. Add a .tsp field within each city,
        2. Create a Road for each pair of cities, and store 'em in two places:
           a) in self.roads, and
           b) in city.roads for each road's city endpoints.
        3. Sort self.roads and city.roads by length.
    """
    self.roads = Roads()
    for city1 in self.cities:
      city1.tsp = self
      for city2 in self.cities:
        if not self.roads.get(city1, city2) and not city1 == city2:
          road = Road(city1, city2)
          for c in (self, city1, city2):
            c.roads.add(road)
    self.roads.update_by_length()
    for city in self.cities:
      city.roads.update_by_length()

  def LK(self, n_tries = 1):
    """ Entry stub for Lin-Kernighan-ish improvement of self.tour .
        If n_tries > 1, the LK algorithm is run multiple times
        on different randomized starting tours, and the best
        result is returned.  (The mean and sd are stored
        in self.lk_tour_mean and self.lk_tour_sigma)
    """
    #
    #
    #
    # The call chain is
    #   LK ->
    #     tour_improve ->
    #         path_search ->
    #              path_search        recursive path modifications
    #                 or
    #              exception back to LK, if 'restart_better_tours'
    for i in range(n_tries):
      if i > 0:
        self.randomize_tour()
        if self.lk_verbose:
          print
          print "RANDOMIZING INITIAL TOUR; trial %i of %i" % (i, n_tries)
          print
      while True:
        try:
          self.tour = self.tour_improve(self.tour)
          break
        except RestartLK:
          pass     # self.tour is now replaced, so just try again
      length = self.tour_length()
      if i == 0:
        best_cities = Cities(self.tour.city_sequence())
        tours = [length]
      else:
        if length < min(tours):
          best_cities = Cities(self.tour.city_sequence())
        tours.append(length)
    self.tour = Tour(self, best_cities)
    self.lk_tour_mean = average(tours)
    self.lk_tour_sigma = stdev(tours)
    if self.lk_verbose:
      print
      print "FINISHED LOOP OVER INITIAL TOURS"
      print " best is %s " % str(self.tour)
      print " lk mean=%8.2f, stdev=%8.2f " % \
            (self.lk_tour_mean, self.lk_tour_sigma)
      print

  def tour_improve(self, tour):
    """ loop over roads ; convert tour to path
        and then start Lin-Kernighan-ish algorithm. """
    (best_length, best_cities) = (tour.tour_length(), tour.city_sequence())

    self._lk_tour_length = tour.tour_length() # best known so far
    loop_roads = Roads(tour) # loop over a duplicate; tour will be modified.
    # loop_roads.update_by_length()  # sort; keeps things deterministic
    # roads_by_length = loop_roads.by_length
    # roads_list = list(tour)

    if self.lk_verbose:
      print "===== starting tour_improve with %i paths to check" % \
            (2*len(loop_roads))
    i = 0
    for road in loop_roads:        # no sort; works, but expect order to vary
    #for road in roads_by_length:  # sorted ... but still not deterministic
    # for road in roads_list:      # still not deterministic.  I give up.
      for backward in (True, False):
        i += 1
        tour.revert()
        tour.tour2path(road, backward)
        if self.lk_verbose:
          print "---- calling %i path_search on %s " % (i, str(tour))
        tour2 = self.path_search(tour)
        if self.lk_verbose:
          print "---- done path_search; found length=%f" % tour2.tour_length()
        if tour2.tour_length() < best_length:
          best_length = tour2.tour_length()
          best_cities = tour2.city_sequence()
    best_tour = Tour(self, best_cities)
    if self.lk_verbose:
      print "===== finished tour_improve; best is %s " % str(best_tour)
    return best_tour

  def path_search(self, path, added=None, deleted=None):
    """ Recursive part of search for an improved TSP solution. """
    if not added:
      added = set()
    if not deleted:
      deleted = set()

    depth = len(added)  # = len(deleted)
    (old_tour_length, old_cities) = (path.tour_length(), path.city_sequence())
    results = [(old_tour_length, old_cities)]
    mods = path.find_lk_mods(added, deleted)

    if self.lk_verbose:
      print " "*depth + "  -- path_search " + \
            " depth=%i, path=%f, tour=%f, n_mods=%i " % \
            (depth, path.length, old_tour_length, len(mods))

    for (city, road_add, road_rm) in mods:

      if self.lk_verbose:
        print " "*depth + "  -> (city, road_add, road_rm) = (%s, %s, %s) " % \
              (str(city), str(road_add), str(road_rm))

      path.modify(city, road_add, road_rm)

      if self.lk_verbose:
        print " "*depth + "  -> modified path %s " % str(path)

      if self.lk_restart_better_tours and \
         (path.tour_length() + 1e-6 < self._lk_tour_length):
          # The 1e-6 is a round-off error fudge factor;
          # I think it sometimes thinks the same tour is a bit shorter,
          # maybe if the roads are added up in a different order.
        self.tour = Tour(self, Cities(path.city_sequence()))
        if self.lk_verbose:
          print "!! restart with better tour ; using %s" % str(self.tour)
        # Restart the whole search, all the back to LK, with this better tour
        raise RestartLK()

      added.add(road_add)
      deleted.add(road_rm)

      if self.lk_depth_limit and depth > self.lk_depth_limit:
        result_path = path
      else:
        result_path = self.path_search(path, added, deleted)
      results.append((result_path.tour_length(), result_path.city_sequence()))

      if self.lk_verbose:
        print " "*depth + "  -> result path=%f; tour=%f" % \
              (result_path.length, result_path.tour_length())

      added.remove(road_add)
      deleted.remove(road_rm)

      path.unmodify(city, road_add, road_rm)

    # Finished breadth search at this depth ; return best result
    (best_length, best_city_seq) = min(results)
    return Tour(self, best_city_seq)

# - - - analysis - - -

def average(numbers):
  """ Return average of a collection of numbers.
      >>> average([1,2,3,4])
      2.5
  """
  return sum(numbers)/(1.0*len(numbers))

def stdev(numbers, sample=True):
  """ Return standard deviation of a collection of numbers.
      If sample=True, use the (n-1) version, treating this as a sample of
      a larger population and giving a best estimate of the parent population.
      >>> "%.5f" % stdev([1,2,3,4], sample=False)
      '1.11803'
      >>> "%.5f" % stdev([1,2,3,4])
      '1.29099'
  """
  # With <x> = average(x)
  # sigma = population standard deviation = <(x-<x>)**2> = <x**2> - <x>**2
  # s = sample standard deviation = sqrt(n/(n-1)) * sigma
  numbers_squared = map(lambda x: x**2, numbers)
  sigma = math.sqrt(average(numbers_squared) - (average(numbers))**2)
  n = float(len(numbers))
  if sample and n > 1:
    return math.sqrt(n/(n-1)) * sigma
  else:
    return sigma

def stats_random_tsp(n_cities, m_times):
  """ Run random_tsp(n) repeatedly, and return
      (avg, stdev) for (time, tour_length, improved_tour_length) """
  times = []
  tour_lengths = []
  tour_lengths_LK = []
  for i in range(m_times):
    (time, tour_length, tour_length_LK) = random_tsp(n_cities)
    times.append(time)
    tour_lengths.append(tour_length)
    tour_lengths_LK.append(tour_length_LK)
  return map(lambda x: (average(x), stdev(x)), \
             (times, tour_lengths, tour_lengths_LK))

def stats_random_samestart(n_cities, m_times):
  """ Run the same n random cities from
      m_times multiple initial starting tours,
      and report on results. """
  tsp = TSP(cities=n_cities, tour='random')
  for i in range(m_times):
    tsp.randomize_tour()
    print "original length = %8.2f " % tsp.tour_length()
    tsp.LK()
    print "lk length = %8.2f" % tsp.tour_length()
    print

def random_tsp(N):
  """ Return (time, tour_length, tour_length_LK)
      for an LK tour improvement with N random cities. """
  start_time = time.clock()
  tsp = TSP(cities=N, tour='random')
  tour_length = tsp.tour_length()
  tsp.LK()
  tour_length_LK = tsp.tour_length()
  return (time.clock() - start_time, tour_length, tour_length_LK)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main():

  # Create the six city example, used for a lot of my tests.
  tsp6 = TSP(cities='test6', tour=('A', 'D', 'C', 'E', 'B', 'F'))

  # So what ya wanna do?
  
  if False:                       # generate an SVG image of the 6 city example
    tsp6.graph('six_cities.svg')
  
  if False:                       # brute force analysis of 6 city example
    print "-- test6 --"
    print tsp6
    tsp6.print_brute_force()

  if False:
    N = 10                        # N=9 brute force : 6 sec ; 10 : 3.5 min (mac laptop)
    tspN = TSP(cities=N, tour='random')
    start_time = time.clock()
    tspN.print_brute_force()
    print "elapsed time: %8.2f sec" % (time.clock() - start_time)

  if False:                      # see the search in action 
    # This spits out a lot of text;
    # best send it to an output file with e.g.
    #   $ python tsp.py > tsp6.out
    tsp6.lk_verbose = True
    tsp6.LK()

  if False:                         # before/after 50 city picture
    print "-- TSP with 50 random cities --"
    tsp50 = TSP(cities=50, tour='random')
    graphname1 = 'random50_before.svg'
    print "  outputting to '%s' ; length = %8.2f" % \
          (graphname1, tsp50.tour_length())
    tsp50.graph(graphname1, all_lines=False, scale=10)
    n_tries = 10
    print "  running LK tour improvement with %i starting tours" % n_tries
    tsp50.LK(n_tries)
    print "  done.  best=%8.2f, mean=%8.2f, sigma=%8.2f " % \
          (tsp50.tour_length(), tsp50.lk_tour_mean, tsp50.lk_tour_sigma)
    graphname2 = 'random50_after.svg'
    print "  outputting to '%s'" % graphname2
    tsp50.graph(graphname2, all_lines=False, scale=10)

  if False:                        # timing for various number of cities
    format_numbers = " %4i   %5.2f  +-%5.2f    %8.2f   %8.2f "
    format_strings = " %4s   %5s  %7s    %8s   %8s "
    print format_strings % ('n', 'time', 'sigma', 'tour', 'lk_tour')
    print format_strings % ('-'*4, '-'*5, '-'*7, '-'*8, '-'*8)
    for n in (5, 10, 20, 40, 80):
      results = stats_random_tsp(n, 8)
      print format_numbers % (n, results[0][0], results[0][1], results[1][0], results[2][0])

  if True:                         # timing for one big TSP
    # Approx times on my mac laptop: N=100: 5sec; N=200: 44 sec; N=300: 200 sec
    N = 300
    print "-- TSP with %i random cities --" % N
    t0 = time.clock()
    tspN = TSP(cities=N, tour='random')
    initial_length = tspN.tour_length()
    t1 = time.clock()
    print (" %.2f sec elapsed : original is " % (t1 - t0)) + str(tspN)
    tspN.LK()
    t2 = time.clock()
    print (" %.2f sec elapsed : LK is " % (t2 - t1)) + str(tspN)

# - - - generic doctest and running main - - - 

#if __name__ == "__main__":
#  doctest.testmod()
#  main()

# - - - code profile analysis  - - - - - - - 

import cProfile
cProfile.run('main()', 'profile_N300.out')
#
# To look at the profile dump,
# see http://docs.python.org/library/profile.html e.g.
#
#   $ python
#   > import pstats
#   > p = pstats.Stats('profile_filename')
#   > p.sort_stats('cumulative').print_stats(10)   # longest 10 functions
#   # or
#   > p.sort_stats('time').print_stats(10)
#
# Here "cumulative" is time spent in a function including sub calls,
# while "time" is the time only in that function, not child calls.
