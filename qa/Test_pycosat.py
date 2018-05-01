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

from solvers import PYCOSAT_Solver

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


##################
#  TEST PYCOSAT  #
##################
class Test_pycosat( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False

  ################
  #  SIMPLOG DM  #
  ################
  def test_simplog_dm( self ) :

    test_id = "simplog_dm"
    test_db = "./IR_" + test_id + ".db"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/simplog_driver.ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c" ]
    argDict[ "EOT" ]      = 4
    argDict[ "EFF" ]      = 2
    argDict[ 'settings' ] = "./settings_files/settings_dm.ini"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      cmd = "mkdir " + argDict[ "data_save_path" ]
      logging.debug( "  TEST SIMPLOG : running cmd = " + cmd )
      os.system( cmd )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    pycosat_solver = PYCOSAT_Solver.PYCOSAT_Solver( argDict, orik_rgg )

    logging.debug( "  SIMPLOG : cnf_fmla_list :" )
    for f in pycosat_solver.cnf_fmla_list :
      logging.debug( f )

    # get all the solns for all the fmlas for the provenance tree
    all_solns = self.get_all_solns( pycosat_solver )

    if self.PRINT_STOP :
      print all_solns
      sys.exit( "hit print stop." )

    expected_all_solns = [["clock(['a','c','1','2'])", "clock(['a','b','1','2'])"], \
                          ["clock(['a','c','1','2'])"], \
                          ["clock(['a','b','1','2'])"], \
                          ["clock(['a','c','1','2'])", "clock(['a','b','1','2'])"], \
                          ["clock(['a','c','1','2'])"], \
                          ["clock(['a','b','1','2'])"], \
                          ["clock(['a','c','1','2'])", "clock(['a','b','1','2'])"], \
                          ["clock(['a','c','1','2'])"], \
                          ["clock(['a','b','1','2'])"]]
    self.assertEqual( all_solns, expected_all_solns )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  #############
  #  SIMPLOG  #
  #############
  def test_simplog( self ) :

    test_id = "simplog"
    test_db = "./IR_" + test_id + ".db"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_id + "_driver.ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c" ]
    argDict[ "EOT" ]      = 4
    argDict[ "EFF" ]      = 2

    if not os.path.exists( argDict[ "data_save_path"] ) :
      cmd = "mkdir " + argDict[ "data_save_path" ]
      logging.debug( "  TEST SIMPLOG : running cmd = " + cmd )
      os.system( cmd )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    pycosat_solver = PYCOSAT_Solver.PYCOSAT_Solver( argDict, orik_rgg )

    logging.debug( "  SIMPLOG : cnf_fmla_list :" )
    for f in pycosat_solver.cnf_fmla_list :
      logging.debug( f )

    # get all the solns for all the fmlas for the provenance tree
    all_solns = self.get_all_solns( pycosat_solver )

    if self.PRINT_STOP :
      print all_solns
      sys.exit( "hit print stop." )

    expected_all_solns = [["clock(['a','b','1','2'])"], ["clock(['a','c','1','2'])"]]
    self.assertEqual( all_solns, expected_all_solns )


    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  ###############
  #  EXAMPLE 1  #
  ###############
  def test_example_1( self ) :

    test_id = "example_1"
    test_db = "./IR_" + test_id + ".db"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./test_files/" + test_id + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c" ]
    argDict[ "EOT" ]      = 1
    argDict[ "EFF" ]      = 0
    argDict[ "settings" ] = "./settings_files/settings_example_1.ini"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      cmd = "mkdir " + argDict[ "data_save_path" ]
      logging.debug( "  TEST EXAMPLE 1 : running cmd = " + cmd )
      os.system( cmd )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    pycosat_solver = PYCOSAT_Solver.PYCOSAT_Solver( argDict, orik_rgg )

    logging.debug( "  EXAMPLE 1 : cnf_fmla_list :" )
    for f in pycosat_solver.cnf_fmla_list :
      logging.debug( f )

    # get all the solns for all the fmlas for the provenance tree
    all_solns = self.get_all_solns( pycosat_solver )

    if self.PRINT_STOP :
      print all_solns
      sys.exit( "hit print stop." )

    expected_all_solns = [["clock(['c','c','1','_'])"], \
                          ["clock(['c','c','1','_'])", "clock(['a','a','1','_'])"], \
                          ["clock(['c','c','1','_'])"], \
                          ["clock(['c','c','1','_'])", "clock(['b','b','1','_'])"]]
    self.assertEqual( all_solns, expected_all_solns )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  ###################
  #  GET ALL SOLNS  #
  ###################
  # a template loop for getting all the solutions.
  # retrieves all the solns across all fmlas generated 
  # from the input provenance tree.
  def get_all_solns( self, pycosat_solver ) :
    all_solns = []
    fmla_id = 0
    soln_id = 0

    while True :

      # make sure fmla exists
      try :
        curr_fmla = pycosat_solver.cnf_fmla_list[ fmla_id ]
      except IndexError :
        logging.debug( "  GET ALL SOLNS : no more fmlas to explore. exiting loop." )
        break # break out of loop. no more solns exist

      # curr_fmla must exist here by defn of previous try-except.
      try :
        logging.debug( "  GET ALL SOLNS : running on fmla_id = " + str( fmla_id ) + ", soln_id = " + str( soln_id ) )
        a_new_soln = pycosat_solver.get_a_soln( curr_fmla, soln_id )
        soln_id   += 1 
        all_solns.append( a_new_soln )
      except IndexError :
        logging.debug( "  GET ALL SOLNS : no more solns to explore wrt to this formula. incrementing to next fmla.")
        fmla_id += 1 # increment to the next fmla
        soln_id  = 0  # reset soln_id
        logging.debug( "  GET ALL SOLNS : incemented fmla_id to " + str( fmla_id ) + ". reseting soln_id." )

    return all_solns


  #########################
  #  GET PROGRAM RESULTS  #
  #########################
  # convert the input dedalus program into c4 datalog and evaluate.
  # return evaluation results dictionary.
  def get_program_results( self, argDict, cursor ) :

    # convert dedalus into c4 datalog
    allProgramData = dedt.translateDedalus( argDict, cursor )

    # run c4 evaluation
    results_array = c4_evaluator.runC4_wrapper( allProgramData[0], argDict )
    parsedResults = tools.getEvalResults_dict_c4( results_array )

    return parsedResults


  ##################
  #  GET ORIK RGG  #
  ##################
  # instantiate and populate a provenance tree structure.
  # return a ProvTree object.
  def get_orik_rgg( self, argDict, inputfile, cursor, test_id ) :

    logging.debug( "  GET ORIK RGG : running process..." )

    # --------------------------------------------------------------- #
    # convert dedalus into c4 datalog and evaluate

    parsedResults = self.get_program_results( argDict, cursor )

    # --------------------------------------------------------------- #
    # generate provenance rgg

    orik_rgg = ProvTree.ProvTree( rootname       = "FinalState", \
                                  parsedResults  = parsedResults, \
                                  cursor         = cursor, \
                                  treeType       = "goal", \
                                  isNeg          = False, \
                                  eot            = argDict[ "EOT" ], \
                                  prev_prov_recs = {}, \
                                  argDict        = argDict )

    orik_rgg.create_pydot_graph( 0, 0, test_id ) # redundant

    logging.debug( "  GET ORIK RGG : running process..." )

    return orik_rgg


  ##################
  #  GET ARG DICT  #
  ##################
  # specify the default test arguments.
  # return dictionary.
  def get_arg_dict( self, inputfile ) :

    # initialize
    argDict = {}

    # populate with unit test defaults
    argDict[ 'prov_diagrams' ]            = False
    argDict[ 'use_symmetry' ]             = False
    argDict[ 'crashes' ]                  = 0
    argDict[ 'solver' ]                   = None
    argDict[ 'disable_dot_rendering' ]    = False
    argDict[ 'settings' ]                 = "./settings_files/settings.ini"
    argDict[ 'negative_support' ]         = False
    argDict[ 'strategy' ]                 = None
    argDict[ 'file' ]                     = inputfile
    argDict[ 'EOT' ]                      = 4
    argDict[ 'find_all_counterexamples' ] = False
    argDict[ 'nodes' ]                    = [ "a", "b", "c" ]
    argDict[ 'evaluator' ]                = "c4"
    argDict[ 'EFF' ]                      = 2
    argDict[ 'data_save_path' ]           = "./data/"

    return argDict


if __name__ == "__main__":
  unittest.main()


#########
#  EOF  #
#########
