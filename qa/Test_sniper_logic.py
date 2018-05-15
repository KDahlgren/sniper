#!/usr/bin/env python

'''
Test_pycosat.py
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

from solvers import sniper_logic

# orik library
if not os.path.abspath( __file__ + "/../../lib/orik/src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../lib/orik/src" ) )

from derivation import ProvTree

# iapyx library
if not os.path.abspath( __file__ + "/../../lib/orik/lib/iapyx/src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../lib/orik/lib/iapyx/src" ) )

from dedt       import dedt
from evaluators import c4_evaluator
from utils      import globalCounters, tools

# ------------------------------------------------------ #


#######################
#  TEST SNIPER LOGIC  #
#######################
class Test_sniper_logic( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False

  #########################
  #  DO ABSORPTION LAW 4  #
  #########################
  def test_do_absorption_law_4( self ) :
    fmla          = "(A&(B|A))|(A|B)"
    expected_fmla = "A|(A|B)"
    self.assertEqual( sniper_logic.do_absorption_law( fmla ), expected_fmla )

  #########################
  #  DO ABSORPTION LAW 3  #
  #########################
  def test_do_absorption_law_3( self ) :
    fmla          = "(A&(B|A))|(A&B)"
    expected_fmla = "A"
    self.assertEqual( sniper_logic.do_absorption_law( fmla ), expected_fmla )

  #########################
  #  DO ABSORPTION LAW 2  #
  #########################
  def test_do_absorption_law_2( self ) :
    fmla          = "A|(A&B)"
    expected_fmla = "A"
    self.assertEqual( sniper_logic.do_absorption_law( fmla ), expected_fmla )

  #########################
  #  DO ABSORPTION LAW 1  #
  #########################
  def test_do_absorption_law_1( self ) :
    fmla          = "A|(B&A)"
    expected_fmla = "A"
    self.assertEqual( sniper_logic.do_absorption_law( fmla ), expected_fmla )

  #########################
  #  DO IDEMPOTENT LAW 4  #
  #########################
  # demonstrates deficiency in idempotence simplification wrt identical expressions
  # around | and & operators.
  @unittest.skip( "need to expand idempotence simplification to expressions." )
  def test_do_idempotent_law_4( self ) :
    fmla          = "(((clock_B)|(clock_B&clock_B))&((clock_A)|clock_A|(clock_A)))"
    fmla          = fmla + "|" + fmla 
    expected_fmla = "(clock_B&clock_A)"
    self.assertEqual( sniper_logic.do_idempotent_law( fmla ), expected_fmla )

  #########################
  #  DO IDEMPOTENT LAW 3  #
  #########################
  def test_do_idempotent_law_3( self ) :
    fmla          = "((A&A)&A)|(A|A|A)|(A&B)"
    expected_fmla = "A|(A&B)"
    self.assertEqual( sniper_logic.do_idempotent_law( fmla ), expected_fmla )

  #########################
  #  DO IDEMPOTENT LAW 2  #
  #########################
  def test_do_idempotent_law_2( self ) :
    fmla          = "(((clock_B)|(clock_B&clock_B&clock_B))&((clock_B)|clock_B|(clock_B)))"
    expected_fmla = "clock_B"
    self.assertEqual( sniper_logic.do_idempotent_law( fmla ), expected_fmla )

  #########################
  #  DO IDEMPOTENT LAW 1  #
  #########################
  def test_do_idempotent_law_1( self ) :
    fmla          = "(((clock_B)|(clock_B&clock_B))&((clock_A)|clock_A|(clock_A)))"
    expected_fmla = "(clock_B&clock_A)"
    self.assertEqual( sniper_logic.do_idempotent_law( fmla ), expected_fmla )


if __name__ == "__main__":
  unittest.main()


#########
#  EOF  #
#########
