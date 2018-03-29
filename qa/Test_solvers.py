#!/usr/bin/env python

'''
Test_solvers.py
'''

#############
#  IMPORTS  #
#############
# standard python packages
import copy, inspect, logging, os, shutil, sqlite3, sys, time, unittest

# ------------------------------------------------------ #
# import sibling packages HERE!!!

if not os.path.abspath( __file__ + "/../../src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../src" ) )

if not os.path.abspath( __file__ + "/../../lib/orik/src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../lib/orik/src" ) )

# ------------------------------------------------------ #


##################
#  TEST SOLVERS  #
##################
class Test_solvers( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False


  ###############
  #  EXAMPLE 1  #
  ###############
  def test_example_1( self ) :
    return None


#########
#  EOF  #
#########
