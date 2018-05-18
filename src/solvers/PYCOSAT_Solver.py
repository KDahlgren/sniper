# modified from https://github.com/palvaro/ldfi-py

# **************************************** #

#############
#  IMPORTS  #
#############
# standard python packages
import re
import pycosat
import ConfigParser, copy, inspect, itertools, logging, os, string, sys, time
import sympy
import sniper_logic

# ------------------------------------------------------ #
# import sibling packages HERE!!!

if not os.path.abspath( __file__ + "/../../../lib/orik/lib/iapyx/src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../../lib/orik/lib/iapyx/src" ) )

from utils import tools


##########################
#  CLASS PYCOSAT SOLVER  #
##########################
class PYCOSAT_Solver( object ) :

  #################
  #  CONSTRUCTOR  #
  #################
  # assume orik rgg input format
  def __init__( self, argDict={}, orik_rgg=None ) :
    self.argDict = argDict

    if argDict == {} and orik_rgg == None :
      return

    # --------------------------------------------------------------- #
    # get configuration params

    try :
      self.POS_FACTS_ONLY = tools.getConfig( self.argDict[ "settings" ], \
                                             "DEFAULT", \
                                             "POS_FACTS_ONLY", \
                                             bool )
    except ConfigParser.NoOptionError :
      self.POS_FACTS_ONLY = True
      logging.warning( "WARNING : no 'POS_FACTS_ONLY' defined in 'DEFAULT' section of " + \
                     self.argDict[ "settings" ] + "...running with POS_FACTS_ONLY==" + \
                     str( self.POS_FACTS_ONLY ) )

    # --------------------------------------------------------------- #
    # need a way to remove duplicates

    self.boolean_fmla_list = self.orik_rgg_to_fmla_list( orik_rgg )
    self.cnf_fmla_list     = self.boolean_fmla_list_to_cnf_fmla_list()

    logging.debug( "  PYCOSAT SOLVER __INIT__ : self.boolean_fmla_list = " + \
                   str( self.boolean_fmla_list ) )
    logging.debug( "  PYCOSAT SOLVER __INIT__ : self.cnf_fmla_list = " + \
                   str( self.cnf_fmla_list ) )


  ################
  #  GET A SOLN  #
  ################
  # calling process will have to pass the fmla of interest and the soln index
  # returns an array of strings representing solns to the fmla in a legible format
  def get_a_soln( self, cnf_fmla, curr_soln_id ) :

    self.list_of_literals  = self.get_list_of_literals( cnf_fmla )

    # https://stackoverflow.com/a/36460020
    # pycosat can't handle literal ids of 0
    literal_to_id_map = { k : v+1 for v, k in enumerate( self.list_of_literals ) }

    # from https://stackoverflow.com/a/483833
    id_to_literal_map = { v : k for k, v in literal_to_id_map.iteritems() }

    # convert to pycosat cnf fmla
    self.pycosat_cnf_fmla = self.cnf_to_pycosat_cnf( cnf_fmla, literal_to_id_map ) # list

    logging.debug( "  GET A SOLN : self.pycosat_cnf_fmla = " + str( self.pycosat_cnf_fmla ) )

    # get the pycosat soln
    a_soln         = list( pycosat.itersolve( self.pycosat_cnf_fmla ) )[ curr_soln_id ]
    a_legible_soln = self.make_soln_legible( a_soln, id_to_literal_map )
    logging.debug( "  GET A SOLN : a_legible_soln = " + str( a_legible_soln ) )

    return a_legible_soln


  #######################
  #  MAKE SOLN LEGIBLE  #
  #######################
  def make_soln_legible( self, a_soln, id_to_literal_map ) :
    logging.debug( "  MAKE SOLN LEGIBLE : a_soln = " + str( a_soln ) )
    logging.debug( "  MAKE SOLN LEGIBLE : id_to_literal_map = " + str( id_to_literal_map )  )
    legible_soln_list_of_literals = []
    for lit_id in a_soln :
      #if not self.POS_FACTS_ONLY and lit_id < 0 :
      #  lit_str = id_to_literal_map[ -1 * lit_id ]
      #  lit_str = "_NOT_" + lit_str
      if lit_id < 0 : # do not include literals mapped to false in the solution
        continue
      else :
        lit_str = id_to_literal_map[ lit_id ]
      lit_str = lit_str.replace( "_RBRKT_", "['" )
      lit_str = lit_str.replace( "_LBRKT_", "']" )
      lit_str = lit_str.replace( "_RPAR_", "(" )
      lit_str = lit_str.replace( "_LPAR_", ")" )
      lit_str = lit_str.replace( "_COMMA_", "','" )
      legible_soln_list_of_literals.append( lit_str )
    return legible_soln_list_of_literals


  ########################
  #  CNF TO PYCOSAT CNF  #
  ########################
  def cnf_to_pycosat_cnf( self, cnf_fmla, literal_to_id_map ) :
    cnf_fmla      = cnf_fmla.translate( None, string.whitespace )
    conjunct_list = cnf_fmla.split( "&" )

    pycosat_list_of_disjuncts = []
    for conjunct in conjunct_list :
      conjunct = conjunct.replace( "(", "" )
      conjunct = conjunct.replace( ")", "" )
      disjuncted_literals = conjunct.split( "|" )
      this_pycosat_disjunctive_clause = []
      for literal in disjuncted_literals :
        if "~" in literal :
          this_pycosat_disjunctive_clause.append( int( "-" + str( literal_to_id_map[ literal.replace( "~", "" ) ] ) ) )
        else :
          this_pycosat_disjunctive_clause.append( literal_to_id_map[ literal ] )
      pycosat_list_of_disjuncts.append( this_pycosat_disjunctive_clause )

    return pycosat_list_of_disjuncts


  ########################################
  #  BOOLEAN FMLA LIST TO CNF FMLA LIST  #
  ########################################
  def boolean_fmla_list_to_cnf_fmla_list( self ) :
     cnf_fmla_list = []
     for boolean_fmla in self.boolean_fmla_list :
       cnf_fmla_list.append( self.get_cnf( boolean_fmla ) )
     return cnf_fmla_list


  #############
  #  GET CNF  #
  #############
  # assumes boolean_fmla is already formatted for sympy
  def get_cnf( self, boolean_fmla ) :

    logging.debug( "  GET CNF : boolean_fmla = " + boolean_fmla )

    # get list of string literals for input into sympy
    #sympy_symbol_list = self.get_list_of_literals( boolean_fmla )
    #symbol_to_id_map, id_to_symbol_map = self.get_literal_maps( sympy_symbol_list )
    #for symb in symbol_to_id_map :
    #  logging.debug( symb + " => " + symbol_to_id_map[ symb ] )
    #boolean_fmla_smaller = self.get_smaller_fmla( boolean_fmla, symbol_to_id_map )
    #logging.debug( "  GET CNF : boolean_fmla_smaller = \n" + boolean_fmla_smaller )
    #sys.exit( "make sure fmlas are simplified" )

    # pass to sympy?
    #cnf_fmla = self.to_cnf_sympy( boolean_fmla, sympy_symbol_list )
    cnf_fmla = self.to_cnf_sympy( boolean_fmla )
    #cnf_fmla = self.to_cnf_sympy( boolean_fmla_smaller )

    logging.debug( "  GET CNF : cnf_fmla = " + str( cnf_fmla ) )
    #sys.exit( "you did it! yay!" )
    return str( cnf_fmla )


  ######################
  #  GET SMALLER FMLA  #
  ######################
  def get_smaller_fmla( self, boolean_fmla, symbol_to_id_map ) :
    for symb in symbol_to_id_map :
      boolean_fmla = boolean_fmla.replace( symb, symbol_to_id_map[ symb ] )
    return boolean_fmla
  
  
  ######################
  #  GET LITERAL MAPS  #
  ######################
  def get_literal_maps( self, sympy_symbol_list ) :
    symbol_to_id_map = {}
    counter = 0
    for symb in sympy_symbol_list :
      if not counter in symbol_to_id_map :
        symbol_to_id_map[ symb ] = "l" + str( counter )
      else :
        raise ValueError( "uh oh. sympy_sybmol_list is not a set. aborting..." )
      counter += 1
    return symbol_to_id_map, {v: k for k, v in symbol_to_id_map.iteritems()}


  ##################
  #  TO CNF SYMPY  #
  ##################
  #def to_cnf_sympy( self, boolean_fmla_sympy, sympy_symbol_list ) :
  def to_cnf_sympy( self, boolean_fmla_sympy, sympy_symbol_list=[] ) :
    if len( sympy_symbol_list ) > 0 :
      self.set_symbols( sympy_symbol_list )
    return sympy.to_cnf( boolean_fmla_sympy )


  #################
  #  SET SYMBOLS  #
  #################
  # to support large numbers of variables,
  # need to feed variables into sympy over the course
  # of multiple symbols() declaration statements.
  def set_symbols( self, sympy_symbol_list ) :

    # conservatively allot at most 3 fmla variables per 
    # symbol( ... ) statement
    sympy_symbol_list_of_triple_arrays = []
    newList                   = []
    for i in range( 0, len( sympy_symbol_list ) ) :
      currsym = sympy_symbol_list[ i ]
      if i % 3 == 0 :
        newList.append( currsym )
        sympy_symbol_list_of_triple_arrays.append( newList )
        newList = []
      elif i + 1 == len( sympy_symbol_list ) :
        newList.append( currsym )
        sympy_symbol_list_of_triple_arrays.append( newList )
        newList = []
      else :
        newList.append( currsym )

    # build and execute symbol statements
    # this process tells sympy the literals used in the input fmla
    # symbol statements are of the form "x,y,z=symbol('x,y,z')"
    for symbol_sublist in sympy_symbol_list_of_triple_arrays :

      # get list of literals without quotes or the starting and ending brackets
      list_of_literals = str( symbol_sublist )
      list_of_literals = list_of_literals.replace( "[", "" )
      list_of_literals = list_of_literals.replace( "]", "" )
      list_of_literals = list_of_literals.replace( '"', "" )
      list_of_literals = list_of_literals.replace( "'", "" )
      list_of_literals = list_of_literals.translate( None, string.whitespace )

      # add to list
      final_statement = list_of_literals + "=sympy.symbols('" + list_of_literals + "')"
      logging.debug( "  SET SYMBOLS : final_statement = " + final_statement )
      exec( final_statement )


  ##########################
  #  GET LIST OF LITERALS  #
  ##########################
  def get_list_of_literals( self, boolean_fmla ) :
    logging.debug( "  GET LIST OF LITERALS : boolean_fmla = " + str( boolean_fmla ) )
    boolean_fmla = boolean_fmla.translate( None, string.whitespace ) # remove all white space
    boolean_fmla = boolean_fmla.replace( "("  , ""           )       # remove all (
    boolean_fmla = boolean_fmla.replace( ")"  , ""           )       # remove all )
    boolean_fmla = boolean_fmla.replace( "~"  , ""           )       # remove all ~
    boolean_fmla = boolean_fmla.replace( "&", "__SOMEOP__" )  # replace ops with some common string
    boolean_fmla = boolean_fmla.replace( "|" , "__SOMEOP__" ) # replace ops with some common string
    literals     = boolean_fmla.split( "__SOMEOP__" )         # get list of literal strings
    literals     = set( literals )                            # remove all duplicates
    literals     = list( literals ) # transform back into list to reduce headaches 
    return literals


  ###########################
  #  ORIK RGG TO FMLA LIST  #
  ###########################
  # create one boolean formula for each post fact
  # only works because final state only has post descendants
  # and post facts only descend from FinalState
  def orik_rgg_to_fmla_list( self, orik_rgg ) :

    fmla_list = []

    logging.debug( "  ORIK RGG TO FMLA LIST : len( orik_rgg.descendants ) = " )
    logging.debug( str( len( orik_rgg.descendants ) ) )
    if orik_rgg.rootname == "FinalState" :
      for d in orik_rgg.descendants :
        logging.debug( "  ORIK RGG TO FMLA LIST : d = " + str( d ) )

    if orik_rgg.rootname == "FinalState" :
      for d in orik_rgg.descendants :
        fmla = self.orik_rgg_to_boolean_fmla( d )
        if not fmla == "()" : # subtree must contain relevant data
          fmla_list.append( fmla )

    logging.debug( "  ORIK RGG TO FMLA LIST : fmla_list = " + str( fmla_list ) )
    return fmla_list


  ##############################
  #  ORIK RGG TO BOOLEAN FMLA  #
  ##############################
  # create one boolean formula for each post fact
  def orik_rgg_to_boolean_fmla( self, orik_rgg ) :

    logging.debug( "=========================================================start" )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : running process..." )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : orik_rgg           : " + str( orik_rgg ) )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : orik_rgg.treeType  : " + str( orik_rgg.treeType ) )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : orik_rgg.descendants : " )
    for d in orik_rgg.descendants :
      logging.debug( d )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : orik_rgg.all_descendant_objs : " )
    for d in orik_rgg.all_descendant_objs :
      logging.debug( str( d ) )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : orik_rgg.all_descendant_objs : " )
    for d in orik_rgg.all_descendant_objs :
      logging.debug( str( d ) )

    this_fmla = ""

    # --------------------------------------------------------- #
    # CASE root is a goal : OR all descendants

    if orik_rgg.treeType == "goal" :

      #for i in range( 0, len( orik_rgg.descendants ) ) :
      #  curr_fmla = self.orik_rgg_to_boolean_fmla( orik_rgg.descendants[ i ] )
      for i in range( 0, len( orik_rgg.all_descendant_objs ) ) :
        curr_fmla = self.orik_rgg_to_boolean_fmla( orik_rgg.all_descendant_objs[ i ] )
        if not curr_fmla == "" and not curr_fmla == "()" :
          if i > 0 :
            #this_fmla += "|" #orig

            # the following makes more sense. breaking this goal
            # requires failing all of the rules.
            this_fmla += "&"
          this_fmla += curr_fmla

    # --------------------------------------------------------- #
    # CASE root is a rule : AND all descendants

    elif orik_rgg.treeType == "rule" :

      #for i in range( 0, len( orik_rgg.descendants ) ) :
      #  curr_fmla = self.orik_rgg_to_boolean_fmla( orik_rgg.descendants[ i ] )
      for i in range( 0, len( orik_rgg.all_descendant_objs ) ) :
        curr_fmla = self.orik_rgg_to_boolean_fmla( orik_rgg.all_descendant_objs[ i ] )
        if not curr_fmla == "" and not curr_fmla == "()" :
          if not this_fmla == "" and i > 0 :
            #this_fmla += "&" #orig

            # the following makes more sense. breaking this rule 
            # requires failing any of the subgoals.
            this_fmla += "|"

          this_fmla += curr_fmla

    # --------------------------------------------------------- #
    # CASE root is a fact : return to string

    elif orik_rgg.treeType == "fact" :
      literal = str( orik_rgg ).translate( None, string.whitespace )

      # remove fact-> references
      literal = literal.replace( "fact->", "" )

      # this check is probably superfluous:
      # ////////////////////////////////////////////////////// #
      # check whether to include only clock facts in fmlas
      try :
        CLOCKS_ONLY = tools.getConfig( self.argDict[ "settings" ], "DEFAULT", "CLOCKS_ONLY", bool )
      except ConfigParser.NoOptionError :
        CLOCKS_ONLY = False
        logging.warning( "WARNING : no 'CLOCKS_ONLY' defined in 'DEFAULT' section of " + \
                       self.argDict[ "settings" ] + "...running with CLOCKS_ONLY==False." )

      logging.debug( "  ORIK RGG TO BOOLEAN FMLA : using CLOCKS_ONLY = " + str( CLOCKS_ONLY ) )
      # ////////////////////////////////////////////////////// #

      if CLOCKS_ONLY and \
         not ( literal.startswith( "clock(" )  or \
               literal.startswith( "_NOT_clock(" ) ) :
        return ""
      else :
        if "_NOT_" in literal :
          literal = "(~" + literal + ")"
        logging.debug( "  ORIK RGG TO BOOLEAN FMLA : returning (1) = " + literal )
        return literal # saves one set of parens

    # --------------------------------------------------------- #
    # post-process string into correct syntax

    # remove all single and double quotes
    this_fmla = this_fmla.replace( "'", "")
    this_fmla = this_fmla.replace( '"', "")

    # replace parens, brackets, and commas
    this_fmla = this_fmla.replace( "[", "_RBRKT_" )
    this_fmla = this_fmla.replace( "]", "_LBRKT_" )
    this_fmla = this_fmla.replace( "(_RBRKT_", "_RPAR__RBRKT_" )
    this_fmla = this_fmla.replace( "_LBRKT_)", "_LBRKT__LPAR_" )
    this_fmla = this_fmla.replace( ",", "_COMMA_" )

    # conserve parentheses
    if this_fmla.startswith( "(" ) and this_fmla.endswith( ")" ) :
      pass
    else :
      #this_fmla = "(" + this_fmla + ")"
      if this_fmla == "" :
        this_fmla = "(" + this_fmla + ")"
      else :
        this_fmla = "(" + str( sympy.simplify( this_fmla ) ) + ")"

    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : orik_rgg : " + str( orik_rgg ) )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : returning (2) " + this_fmla )
    logging.debug( "=========================================================end" )
    return this_fmla


  ###############
  #  IS BINARY  #
  ###############
  def is_binary( self, fmla ) :
    p = re.compile( "\w+" )
    if fmla.startswith( "(" ) and \
       fmla.endswith( ")" )   and \
       len( p.findall( fmla ) ) == 2 :
      return True
    else :
      return False


  ################
  #  IS LITERAL  #
  ################
  def is_literal( self, fmla ) :
    if not "&" in fmla and not "|" in fmla :
      return True
    else :
      return False


  #################
  #  SAFE PARENS  #
  #################
  def safe_parens( self, fmla ) :
    logging.debug( "  SAFE PARENS : fmla = " + fmla )
    num_open_parens = 0
    num_closed_parens = 0
    for char in fmla :
      if char == "(" :
        num_open_parens += 1
      elif char == ")" :
        num_closed_parens += 1
      if not num_open_parens >= num_closed_parens :
        logging.debug( "  SAFE PARENS : returning False (1)" )
        return False
    if num_open_parens < 1 :
      logging.debug( "  SAFE PARENS : returning False (2)" )
      return False
    else :
      logging.debug( "  SAFE PARENS : returning True" )
      return True


  ##################
  #  IS SELF COMM  #
  ##################
  # only works on clock literal inputs
  def is_self_comm( self, clock_literal ) :
    logging.debug( "  IS SELF COMM : clock_literal = " + clock_literal )
    data_list = self.get_data_list( clock_literal )
    logging.debug( "  IS SELF COMM : data_list = " + str( data_list ) )
    if data_list[ 0 ] == data_list[ 1 ] :
      logging.debug( "  IS SELF COMM : returning True" )
      return True
    else :
      logging.debug( "  IS SELF COMM : returning False" )
      return False

  ###################
  #  IS NODE CRASH  #
  ###################
  # only works on clock literal inputs
  def is_node_crash( self, clock_literal ) :
    logging.debug( "  IS NODE CRASH : clock_literal = " + clock_literal )
    data_list = self.get_data_list( clock_literal )
    if data_list[ 1 ] == "_" :
      logging.debug( "  IS NODE CRASH : returning True" )
      return True
    else :
      logging.debug( "  IS NODE CRASH : returning False" )
      return False

  ###################
  #  GET DATA LIST  #
  ###################
  def get_data_list( self, literal ) :
    literal = literal[ literal.find( "([" ) : ] # remove relation name and prepend
    literal = literal.replace( "([", "" )       # remove end bit
    literal = literal.replace( "])", "" )       # remove end bit
    literal = literal.replace( "'", "" )        # remove quotes
    literal = literal.replace( '"', "" )        # remove quotes
    return literal.split( "," )


#########
#  EOF  #
#########
