#!/usr/bin/env python

'''
Test_z3.py
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

from solvers import Z3_Solver

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


#############
#  TEST Z3  #
#############
class Test_z3( unittest.TestCase ) :

  logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.DEBUG )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO )
  #logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.WARNING )

  PRINT_STOP = False

  ###############
  #  REPLOG DM  #
  ###############
  #@unittest.skip( "works." )
  def test_replog_dm( self ) :

    test_id        = "replog_dm"
    test_file_name = "replog_driver"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    test_db = "./IR_" + test_id + ".db"

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_file_name + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c" ]
    argDict[ "EOT" ]      = 6
    argDict[ "EFF" ]      = 3
    argDict[ "settings" ] = "./settings_files/settings_dm_allow_not_clocks.ini"
    argDict[ "data_save_path" ] = "./data/" + test_id + "/"

    if not os.path.exists( argDict[ "data_save_path" ] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    z3_solver = Z3_Solver.Z3_Solver( argDict, orik_rgg )
    a_soln    = z3_solver.get_a_soln()

    if self.PRINT_STOP :
      print a_soln
      sys.exit( "hit print stop." )

    expected_soln = ["clock(['a','b','1','2'])", \
                     "clock(['a','c','1','2'])", \
                     "clock(['a','b','2','3'])", \
                     "clock(['a','c','2','3'])"]
    self.assertEqual( a_soln, expected_soln )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  ###################
  #  CLASSIC RB DM  #
  ###################
  #@unittest.skip( "works." )
  def test_classic_rb_dm( self ) :

    test_id        = "classic_rb_dm"
    test_file_name = "classic_rb_driver"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    test_db = "./IR_" + test_id + ".db"

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_file_name + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c" ]
    argDict[ "EOT" ]      = 6
    argDict[ "EFF" ]      = 3
    argDict[ "settings" ] = "./settings_files/settings_dm_allow_not_clocks.ini"
    argDict[ "data_save_path" ] = "./data/" + test_id + "/"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    z3_solver = Z3_Solver.Z3_Solver( argDict, orik_rgg )
    a_soln    = z3_solver.get_a_soln()

    if self.PRINT_STOP :
      print a_soln
      sys.exit( "hit print stop." )

    expected_soln = ["clock(['a','b','1','2'])", \
                     "clock(['a','c','1','2'])"]
    self.assertEqual( a_soln, expected_soln )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )



  ##############
  #  KAFKA DM  #
  ##############
  @unittest.skip( "stalling at c4." )
  def test_kafka_dm( self ) :

    test_id        = "kafka_dm"
    test_file_name = "kafka_driver"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    test_db = "./IR_" + test_id + ".db"

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_file_name + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c", "C", "Z" ]
    argDict[ "EOT" ]      = 7
    argDict[ "EFF" ]      = 4
    argDict[ "settings" ] = "./settings_files/settings_dm_allow_not_clocks.ini"
    argDict[ "data_save_path" ] = "./data/" + test_id + "/"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    z3_solver = Z3_Solver.Z3_Solver( argDict, orik_rgg )
    a_soln    = z3_solver.get_a_soln()

    if self.PRINT_STOP :
      print a_soln
      sys.exit( "hit print stop." )

    expected_soln = ["_NOT_clock(['Node1','Server','2','1'])", \
                     "clock(['Node1','Server','1','2'])", \
                     "_NOT_clock(['Node1','Server','1','1'])", \
                     "_NOT_clock(['Node2','Server','2','1'])", \
                     "_NOT_clock(['Node1','Server','3','1'])", \
                     "_NOT_clock(['Node2','Server','1','1'])", \
                     "_NOT_clock(['Node2','Server','3','1'])"]
    self.assertEqual( a_soln, expected_soln )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  ###########
  #  KAFKA  #
  ###########
  #@unittest.skip( "works." )
  def test_kafka( self ) :

    test_id        = "kafka"
    test_file_name = "kafka_driver"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    test_db = "./IR_" + test_id + ".db"

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_file_name + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c", "C", "Z" ]
    argDict[ "EOT" ]      = 7
    argDict[ "EFF" ]      = 4
    argDict[ "settings" ] = "./settings_files/settings.ini"
    argDict[ "data_save_path" ] = "./data/" + test_id + "/"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    z3_solver = Z3_Solver.Z3_Solver( argDict, orik_rgg )
    a_soln    = z3_solver.get_a_soln()

    if self.PRINT_STOP :
      print a_soln
      sys.exit( "hit print stop." )

    expected_soln = ["clock(['a','c','5','6'])", \
                     "clock(['a','b','5','6'])", \
                     "clock(['a','C','6','7'])", \
                     "clock(['C','a','3','4'])"]
    self.assertEqual( a_soln, expected_soln )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  #############
  #  ASYNC 1  #
  #############
  #@unittest.skip( "works." )
  def test_async_1( self ) :

    test_id        = "async_1"
    test_file_name = "async_1_driver"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    test_db = "./IR_" + test_id + ".db"

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_file_name + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "Node1", "Node2", "Server" ]
    argDict[ "EOT" ]      = 3
    argDict[ "EFF" ]      = 0
    argDict[ "settings" ] = "./settings_files/settings_dm_allow_not_clocks.ini"
    argDict[ "data_save_path" ] = "./data/" + test_id + "/"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    z3_solver = Z3_Solver.Z3_Solver( argDict, orik_rgg )
    a_soln    = z3_solver.get_a_soln()

    if self.PRINT_STOP :
      print "PRINTING A SOLN:"
      print a_soln
      #res = z3_solver.get_all_solns()
      #print len( res )
      sys.exit( "hit print stop." )

    expected_soln = ["clock(['Node1','Server','1','2'])"]
    self.assertEqual( a_soln, expected_soln )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  ################
  #  SIMPLOG DM  #
  ################
  #@unittest.skip( "works." )
  def test_simplog_dm( self ) :

    test_id        = "simplog_dm"
    test_file_name = "simplog_driver"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    test_db = "./IR_" + test_id + ".db"

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_file_name + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c" ]
    argDict[ "EOT" ]      = 4
    argDict[ "EFF" ]      = 2
    argDict[ "settings" ] = "./settings_files/settings_dm.ini"
    argDict[ "data_save_path" ] = "./data/" + test_id + "/"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    z3_solver = Z3_Solver.Z3_Solver( argDict, orik_rgg )
    a_soln = z3_solver.get_a_soln()
    expected_a_soln = ["clock(['a','b','1','2'])", "clock(['a','c','1','2'])"]

    # get all the solns for all the fmlas for the provenance tree
    all_solns = z3_solver.get_all_solns()

    if self.PRINT_STOP :
      print all_solns
      sys.exit( "hit print stop." )

    expected_all_solns = [ ["clock(['a','b','1','2'])", "clock(['a','c','1','2'])"], \
                           ["clock(['a','b','1','2'])"], \
                           ["clock(['a','c','1','2'])"] ]

    self.assertEqual( a_soln, expected_a_soln )
    self.assertEqual( all_solns, expected_all_solns )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


  #############
  #  SIMPLOG  #
  #############
  #@unittest.skip( "works." )
  def test_simplog( self ) :

    test_id        = "simplog"
    test_file_name = "simplog_driver"

    logging.debug( ">> RUNNING TEST '" + test_id + "' <<<" )

    # --------------------------------------------------------------- #
    # set up test

    test_db = "./IR_" + test_id + ".db"

    if os.path.exists( test_db ) :
      os.remove( test_db )

    IRDB   = sqlite3.connect( test_db )
    cursor = IRDB.cursor()

    dedt.createDedalusIRTables(cursor)
    dedt.globalCounterReset()

    # --------------------------------------------------------------- #
    # specify input file paths

    inputfile = "./dedalus_drivers/" + test_file_name + ".ded"

    # --------------------------------------------------------------- #
    # get argDict

    argDict = self.get_arg_dict( inputfile )
    argDict[ "nodes" ]    = [ "a", "b", "c" ]
    argDict[ "EOT" ]      = 4
    argDict[ "EFF" ]      = 2
    argDict[ "settings" ] = "./settings_files/settings.ini"
    argDict[ "data_save_path" ] = "./data/" + test_id + "/"

    if not os.path.exists( argDict[ "data_save_path"] ) :
      self.make_data_dir( argDict[ "data_save_path" ], test_id )

    # --------------------------------------------------------------- #
    # generate orik rgg

    orik_rgg = self.get_orik_rgg( argDict, \
                                  inputfile, \
                                  cursor, \
                                  test_id )

    # --------------------------------------------------------------- #
    # generate fault hypotheses

    z3_solver = Z3_Solver.Z3_Solver( argDict, orik_rgg )

    # get all the solns for all the fmlas for the provenance tree
    all_solns = z3_solver.get_all_solns()

    if self.PRINT_STOP :
      print all_solns
      sys.exit( "hit print stop." )

    expected_all_solns = [ ["clock(['a','b','1','2'])"], \
                           ["clock(['a','c','1','2'])"] ]
    self.assertEqual( all_solns, expected_all_solns )

    # --------------------------------------------------------------- #
    # clean up yo mess

    if os.path.exists( test_db ) :
      os.remove( test_db )


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


  ###################
  #  MAKE DATA DIR  #
  ###################
  def make_data_dir( self, data_save_path, test_id ) :
    logging.debug( "  TEST " + test_id.upper() + \
                   " : data save path not found : " + \
                   data_save_path )

    dir_list = data_save_path.split( "/" )
    complete_str = "./"
    for this_dir in dir_list :
      if this_dir == "./" :
        complete_str += this_dir
      else :
        complete_str += this_dir + "/"
        if not os.path.exists( complete_str ) :
          cmd = "mkdir " + complete_str
          logging.debug( "  TEST " + test_id.upper() + " : running cmd = " + cmd )
          os.system( cmd )


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


##############################
#  MAIN THREAD OF EXECUTION  #
##############################
if __name__ == "__main__":
  unittest.main()


#########
#  EOF  #
#########
