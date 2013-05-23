'''
Created on 23.05.2013

@author: Tambet
'''
'''
Lin-Kernighan algorithm

1. Generate a random initial tour T.
2. Let i = 1. Choose t1.
3. Choose x1 = (t1,t2) Î T.
4. Choose y1 = (t2,t3) Ï T such that G1 > 0.
If this is not possible, go to Step 12.
5. Let i = i+1.
6. Choose xi = (t2i-1,t2i) Î T such that
(a) if t2i is joined to t1, the resulting configuration is a
tour, T’, and
(b) xi ¹ ys for all s < i.
If T’ is a better tour than T, let T = T’ and go to Step 2.
7. Choose yi = (t2i,t2i+1) Ï T such that
(a) Gi > 0,
(b) yi ¹ xs for all s £ i, and
(c) xi+1 exists.
If such yi exists, go to Step 5.
8. If there is an untried alternative for y2, let i = 2 and go to Step 7.
9. If there is an untried alternative for x2, let i = 2 and go to Step 6.
10. If there is an untried alternative for y1, let i = 1 and go to Step 4.
11. If there is an untried alternative for x1, let i = 1 and go to Step 3.
12. If there is an untried alternative for t1, then go to Step 2.
13. Stop (or go to Step 1).

'''
print "and so it begins"