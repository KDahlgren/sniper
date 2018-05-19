# **************************************** #

#############
#  IMPORTS  #
#############
# standard python packages
import z3
import ConfigParser, copy, logging, os, string, sys

# ------------------------------------------------------ #
# import sibling packages HERE!!!

if not os.path.abspath( __file__ + "/../../../lib/orik/lib/iapyx/src" ) in sys.path :
  sys.path.append( os.path.abspath( __file__ + "/../../../lib/orik/lib/iapyx/src" ) )

from utils import tools


#####################
#  CLASS Z3 SOLVER  #
#####################
class Z3_Solver( object ) :

  #################
  #  CONSTRUCTOR  #
  #################
  # assume orik rgg input format
  def __init__( self, argDict={}, orik_rgg=None ) :
    self.argDict     = argDict
    self.solver_type = "z3"

    if argDict == {} and orik_rgg == None :
      return

    # --------------------------------------------------------------- #
    # get configuration params

    # ========= POS_FACTS_ONLY ========== #
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

    # ========= USE_INTERMEDIATE_SIMPLIFICATIONS ========== #
    try :
      self.USE_INTERMEDIATE_SIMPLIFICATIONS = tools.getConfig( self.argDict[ "settings" ], \
                                                        "DEFAULT", \
                                                        "USE_INTERMEDIATE_SIMPLIFICATIONS", \
                                                        bool )
    except ConfigParser.NoOptionError :
      self.USE_INTERMEDIATE_SIMPLIFICATIONS = False
      logging.warning( "WARNING : no 'USE_INTERMEDIATE_SIMPLIFICATIONS' " + \
                       "defined in 'DEFAULT' section of "+ \
                     self.argDict[ "settings" ] + "...running with " + \
                     "USE_INTERMEDIATE_SIMPLIFICATIONS ==" + \
                     str( self.USE_INTERMEDIATE_SIMPLIFICATIONS ) )

    # ========= CLOCKS_ONLY ========== #
    try :
      self.CLOCKS_ONLY = tools.getConfig( self.argDict[ "settings" ], \
                                          "DEFAULT", \
                                          "CLOCKS_ONLY", \
                                          bool )
    except ConfigParser.NoOptionError :
      self.CLOCKS_ONLY = False
      logging.warning( "WARNING : no 'CLOCKS_ONLY' defined in 'DEFAULT' section of " + \
                       self.argDict[ "settings" ] + "...running with CLOCKS_ONLY==False." )

    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : using CLOCKS_ONLY = " + str( self.CLOCKS_ONLY ) )

    # --------------------------------------------------------------- #

    self.boolean_fmla_list_orig               = self.orik_rgg_to_fmla_list( orik_rgg )
    literal_to_id_map, self.id_to_literal_map = self.get_literal_maps()
    self.boolean_fmla_list                    = self.get_smaller_fmlas( literal_to_id_map )

    logging.debug( "  Z3 SOLVER __INIT__ : self.boolean_fmla_list_orig = " + \
                   str( self.boolean_fmla_list_orig ) )
    logging.debug( "  Z3 SOLVER __INIT__ : literal_to_id_map = " + \
                   str( literal_to_id_map ) )
    logging.debug( "  Z3 SOLVER __INIT__ : self.id_to_literal_map = " + \
                   str( self.id_to_literal_map ) )
    logging.debug( "  Z3 SOLVER __INIT__ : self.boolean_fmla_list = " + \
                   str( self.boolean_fmla_list ) )

    # --------------------------------------------------------------- #
    # other persistent data

    self.s                         = z3.Solver()
    self.fmla_id                   = 0
    self.prev_fmla_id              = self.fmla_id
    self.set_symbols_statement     = None
    self.constraint_statement_list = []
    self.previously_found_solns    = []


  #######################
  #  GET SMALLER FMLAS  #
  #######################
  def get_smaller_fmlas( self, literal_to_id_map ) :

    smaller_list = []

    for fmla in self.boolean_fmla_list_orig :
      for lit in literal_to_id_map :
        fmla = fmla.replace( lit, literal_to_id_map[ lit ] )
      smaller_list.append( fmla )

    return list( set( smaller_list ) ) # remove duplicates


  ######################
  #  GET LITERAL MAPS  #
  ######################
  # map all literals in the boolean fmla to unique
  # strings of the form 'l<integer>'.
  # also provide the flipped map.
  def get_literal_maps( self ) :

    # generate the set of all literals
    list_of_literals = []
    for fmla in self.boolean_fmla_list_orig :
      list_of_literals.extend( self.get_list_of_literals( fmla ) )
    list_of_literals = list( set( list_of_literals ) ) # remove duplicates

    # register literals with z3
    #self.set_z3_symbols( list_of_literals )

    logging.debug( "  GET LITERAL MAPS : list_of_literals = " )
    logging.debug( list_of_literals )

    # from https://stackoverflow.com/a/36460020
    literal_to_id_map = { k : 'l' + str( v+1 ) for v, k in enumerate( list_of_literals ) }

    # from https://stackoverflow.com/a/483833
    id_to_literal_map = { v : k for k, v in literal_to_id_map.iteritems() }

    logging.debug( "  GET LITERAL MAPS : literal_to_id_map = " )
    logging.debug( literal_to_id_map )

    return literal_to_id_map, id_to_literal_map


  ####################
  #  SET Z3 SYMBOLS  #
  ####################
  # to support large numbers of variables,
  # need to feed variables into z3 over the course
  # of multiple symbols() declaration statements.
  def set_z3_symbols( self, symbol_list ) :

    # get list of literals without quotes or the starting and ending brackets
    list_of_literals = str( symbol_list )
    list_of_literals = list_of_literals.translate( None, string.whitespace )
    list_of_literals = list_of_literals.replace( "[", "" )
    list_of_literals = list_of_literals.replace( "]", "" )
    list_of_literals = list_of_literals.replace( '"', "" )
    list_of_literals = list_of_literals.replace( "'", "" )
    list_of_literals = list_of_literals.replace( ",", ", " )

    if list_of_literals.startswith( ", " ) :
      list_of_literals = list_of_literals[2:]

    final_statement = list_of_literals + " = z3.Bools('" + list_of_literals.replace( ",", "" ) + "')"
    logging.debug( "  SET SYMBOLS : final_statement : " + final_statement )
    #exec( final_statement )
    return final_statement


  ##########################
  #  GET LIST OF LITERALS  #
  ##########################
  def get_list_of_literals( self, boolean_fmla ) :
    logging.debug( "  GET LIST OF LITERALS : boolean_fmla = " + str( boolean_fmla ) )
    boolean_fmla = boolean_fmla.translate( None, string.whitespace ) # remove all white space
    boolean_fmla = boolean_fmla.replace( "("  , ""  )                # remove all (
    boolean_fmla = boolean_fmla.replace( ")"  , ""  )                # remove all )
    boolean_fmla = boolean_fmla.replace( "~"  , ""  )                # remove all ~
    boolean_fmla = boolean_fmla.replace( "And", ""  )                # remove all And
    boolean_fmla = boolean_fmla.replace( "Or" , ""  )                # remove all Or
    boolean_fmla = boolean_fmla.replace( "Not" , "" )                # remove all Not
    boolean_fmla = boolean_fmla.replace( "z3." , "" )                # remove all z3.
    literals     = boolean_fmla.split( "," ) # get list of literal strings
    literals     = list( set( literals ) )   # remove all duplicates

    logging.debug( "  GET LIST OF LITERALS : literals = " + str( literals ) )
    return literals


  ################
  #  GET A SOLN  #
  ################
  # grab a soln found by the z3 solver.
  # observe this does not handle remembering previous solutions by default.
  def get_a_soln( self, fmla_id=0, add_constraint=False ) :

    logging.debug( "  GET A SOLN : fmla_id        = " + str( fmla_id ) )
    logging.debug( "  GET A SOLN : add_constraint = " + str( add_constraint ) )

    added_a_constraint = False
    while True : # loop until you find a non-empty soln_array

      # define fmla to solve
      this_fmla = self.boolean_fmla_list[ fmla_id ]
      logging.debug( "  GET A SOLN : solving fmla '" + this_fmla + "'" )
  
      symbol_list = self.get_list_of_literals( this_fmla )
      if self.set_symbols_statement == None :
        self.set_symbols_statement = self.set_z3_symbols( symbol_list )
        exec( self.set_symbols_statement )
  
      # ----------------------------------------------------------------------- #
      #                            RESET SOLVER

      if self.fmla_id == 0 :
        self.reset_solver( this_fmla, symbol_list )  

      if self.fmla_id > self.prev_fmla_id :
        #self.fmla_id      += 1
        self.prev_fmla_id = self.fmla_id
        self.reset_solver( this_fmla, symbol_list )
  
      # ----------------------------------------------------------------------- #
  
      self.s.check()
      logging.debug( "  GET A SOLN : self.s.check() = " + str( self.s.check() ) )
      logging.debug( "  GET A SOLN : self.s.model() = " + str( self.s.model() ) )
  
      # collect solutions
      constraint_list = ""
      soln_array          = []
      for i in range( 0, len( symbol_list ) ) :
        lit = symbol_list[ i ]
  
        # need to convert literals into z3 Boolean objects for this to work.
        z3_lit = eval( "z3.Bool('" + lit + "')" )
  
        logging.debug( "  GET A SOLN : self.s.model()[ " + str( z3_lit ) + " ] = " + \
                       str( self.s.model()[ z3_lit ] ) )
  
        if self.s.model()[ z3_lit ] == True :
          soln_array.append( self.make_legible( self.id_to_literal_map[ lit ] ) )
  
        # handle constraints for non-literal fmlas
        if not self.is_literal( this_fmla ) :
          # define Trues and Falses
          if self.s.model()[ z3_lit ] == None :
            constraint_list += lit + " != " + str( False )
          else :
            constraint_list += lit + " != " + str( self.s.model()[ z3_lit ] )
    
          # add commas
          if i < len( symbol_list )-1 :
            constraint_list += ", "
  
        # handle constraints for literal fmlas
        else :
          constraint_list = "False"
  
      # add to list of previously considered solns
      # ex. s.add( Or(a != s.model()[a], b != s.model()[b]))
      #  says "in the future, make sure a and b never match this combination of values."
      if len( soln_array ) < 1 or add_constraint :
        self.save_soln_elimination_constraints( constraint_list )
        added_a_constraint = True
      elif added_a_constraint :
        self.reset_solver( this_fmla, symbol_list )

      if len( soln_array ) > 0 :
        break

    logging.debug( "  GET A SOLN : soln_array : " + str( soln_array ) )
    return soln_array


  ################
  #  IS LITERAL  #
  ################
  # check if the input fmla contains only a literal
  def is_literal( self, this_fmla ) :
    if not "z3.And"  in this_fmla and \
       not "z3.Or"   in this_fmla and \
       not "z3.Not" in this_fmla :
      return True
    else :
      return False


  #######################################
  #  SAVE SOLN ELIMINATION CONSTRAINTS  #
  #######################################
  def save_soln_elimination_constraints( self, constraint_list ) :
    exec( self.set_symbols_statement ) # need to do this here too???
    constraint_statement = "z3.Or(" + constraint_list + ")" 
    logging.debug( "  SAVE SOLN ELIMINATION CONSTRAINTS : constraint_statement = " + \
                   constraint_statement )

    # be sure to not introduce duplicates
    if not constraint_statement in self.constraint_statement_list :
      self.constraint_statement_list.append( constraint_statement )

    self.s.add( eval( constraint_statement ) )


  #########################################
  #  REPLAY SOLN ELIMINATION CONSTRAINTS  #
  #########################################
  def replay_soln_elimination_constraints( self ) :
    exec( self.set_symbols_statement ) # need to do this here too???
    for constraint_statement in self.constraint_statement_list :

      if constraint_statement == "z3.Or(False)" :
        logging.debug( "  REPLAY SOLN ELIMINATION CONSTRAINTS : hit a 'False' " + \
                       "constraint. skipping." )
        pass

      else :
        logging.debug( "  REPLAY SOLN ELIMINATION CONSTRAINTS : self.s.check() = " + \
                       str( self.s.check() ) )
        logging.debug( "  REPLAY SOLN ELIMINATION CONSTRAINTS : constraint_statement (before) = " + \
                       constraint_statement )
        self.s.add( eval( constraint_statement ) )
        logging.debug( "  REPLAY SOLN ELIMINATION CONSTRAINTS : self.s.check() (after) = " + \
                       str( self.s.check() ) )


  ##################
  #  RESET SOLVER  #
  ##################
  def reset_solver( self, boolean_fmla, symbol_list ) :
    logging.debug( "  RESET SOLVER : running..." )
    logging.debug( "  RESET SOLVER : boolean_fmla = " + boolean_fmla ) 

    # clear object
    self.s = None
    self.s = z3.Solver()

    # set z3 symbols
    self.set_symbols_statement = self.set_z3_symbols( symbol_list )
    exec( self.set_symbols_statement ) # need to do this here too for some reason???

    # add the input boolean fmla
    #soln_array = z3.solve( eval( boolean_fmla ) )
    self.s.add( eval( boolean_fmla ) ) # need eval statement.
    self.s.check() # need to do this before calling model()
    logging.debug( "  RESET SOLVER : self.s.check() = " + str( self.s.check() ) )

    # replay previously considered solutions
    self.replay_soln_elimination_constraints()

    logging.debug( "  RESET SOLVER : ...done." )


  ###################
  #  GET NEXT SOLN  #
  ###################
  # grab new solns not found previously.
  def get_next_soln( self ) :
    logging.debug( "  GET NEXT SOLN : self.s.check() = " + str( self.s.check() ) )
    logging.debug( "  GET NEXT SOLN : self.constraint_statement_list = \n" + \
                   str( self.constraint_statement_list ) )
    logging.debug( "  GET NEXT SOLN : self.previously_found_solns = \n" + \
                   str( self.previously_found_solns ) )

    # if the current fmla is unsatisfiable, get another formula
    if self.s.check() == z3.unsat :

      while True :

        # increment the fmla identifier
        self.fmla_id += 1
        logging.debug( "  GET NEXT SOLN : self.fmla_id = " + str( self.fmla_id ) )
  
        try :
          self.boolean_fmla_list[ self.fmla_id ]
          logging.debug( "  GET NEXT SOLN : checking for solns in fmla " + \
                         "self.boolean_fmla_list[ " + str( self.fmla_id ) + " ] : \n'" + \
                         self.boolean_fmla_list[ self.fmla_id ] + "'"  )
  
          # check if this fmla has a soln
          try :
            next_soln = self.get_a_soln( fmla_id=self.fmla_id, add_constraint=True )
            if not next_soln in self.previously_found_solns :
              self.previously_found_solns.append( next_soln )
              break # break loop 'cause you found a new one.
            else :
              pass

          except z3.Z3Exception :
            logging.debug( "  GET NEXT SOLN : fmla has no new solns." )
            continue # see if another fmla exists.
  
        except IndexError :
          # break the loop 'cause you ran out of fmlas
          logging.debug( "  GET NEXT SOLN : no more fmlas to check." )
          return "no more fmlas to check."

    # otherwise, get the next solution for this formula.
    else :
      while True :
        next_soln = self.get_a_soln( self.fmla_id, add_constraint=True )
        if not next_soln in self.previously_found_solns :
          self.previously_found_solns.append( next_soln )
          break

    logging.debug( "  GET NEXT SOLN : next_soln = " + str( next_soln ) )
    return next_soln


  ###################
  #  GET ALL SOLNS  #
  ###################
  # grab all solns.
  def get_all_solns( self ) :
    all_solns = []
    COUNTER = 0
    while True :
      print "COUNTER = " + str( COUNTER )
      new_soln = self.get_next_soln()
      if new_soln == "no more fmlas to check." :
        break
      else :
        all_solns.append( new_soln )
      #if COUNTER > 50 :
      #  sys.exit( "hit over " + str( COUNTER ) + " solns. you sure bro? aborting..." )
      COUNTER += 1
    return all_solns


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
        if not fmla == "" : # subtree must contain relevant data
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
    prev_integrated = []

    # --------------------------------------------------------- #
    # CASE root is a goal : OR all descendants

    if orik_rgg.treeType == "goal" :
      for i in range( 0, len( orik_rgg.all_descendant_objs ) ) :
        curr_fmla = self.orik_rgg_to_boolean_fmla( orik_rgg.all_descendant_objs[ i ] )
        if not curr_fmla == "" :
          if not curr_fmla in prev_integrated :
            if not this_fmla == "" and i > 0 :
              this_fmla += ","
            prev_integrated.append( curr_fmla )
            this_fmla += curr_fmla
      if "," in this_fmla :
        #this_fmla = "z3.Or(" + this_fmla + ")" #orig
        this_fmla = "z3.And(" + this_fmla + ")"

    # --------------------------------------------------------- #
    # CASE root is a rule : AND all descendants

    elif orik_rgg.treeType == "rule" :
      for i in range( 0, len( orik_rgg.all_descendant_objs ) ) :
        curr_fmla = self.orik_rgg_to_boolean_fmla( orik_rgg.all_descendant_objs[ i ] )
        if not curr_fmla == "" :
          if not curr_fmla in prev_integrated :
            if not this_fmla == "" and i > 0 :
              this_fmla += ","
            prev_integrated.append( curr_fmla )
            this_fmla += curr_fmla
      if "," in this_fmla :
        #this_fmla = "z3.And(" + this_fmla + ")"  #orig
        this_fmla = "z3.Or(" + this_fmla + ")"

    # --------------------------------------------------------- #
    # CASE root is a fact : return to string

    elif orik_rgg.treeType == "fact" :
      literal = str( orik_rgg ).translate( None, string.whitespace )

      if self.CLOCKS_ONLY and \
         not ( literal.startswith( "fact->clock(" )  or \
               literal.startswith( "fact->_NOT_clock(" ) ) :
        return ""
      else :

        # remove all single and double quotes
        literal = literal.replace( "'", "")
        literal = literal.replace( '"', "")

        # remove fact-> references
        literal = literal.replace( "fact->", "" )

        # replace parens, brackets, and commas
        literal = literal.replace( "[", "_RBRKT_" )
        literal = literal.replace( "]", "_LBRKT_" )
        literal = literal.replace( "(_RBRKT_", "_RPAR__RBRKT_" )
        literal = literal.replace( "_LBRKT_)", "_LBRKT__LPAR_" )
        literal = literal.replace( ",", "_COMMA_" )

        # replace negations
        #this_fmla = this_fmla.replace( "_NOT_", "~" )
        if "_NOT_" in literal :
          literal = "z3.Not(" + literal + ")"

        logging.debug( "  ORIK RGG TO BOOLEAN FMLA : returning (1) = " + literal )
        return literal

    # --------------------------------------------------------- #

    if self.USE_INTERMEDIATE_SIMPLIFICATIONS :
      if this_fmla.startswith( "z3.And(" ) or \
         this_fmla.startswith( "z3.Or(" ) or \
         this_fmla.startswith( "z3.Not(" ) :

        # register symbols with z3
        symbol_list           = self.get_list_of_literals( this_fmla )
        set_symbols_statement = self.set_z3_symbols( symbol_list )
        exec( set_symbols_statement ) # need to do this here too for some reason???

        # perform simplification
        # note the default fast solver doesn't 
        # perform absorption https://stackoverflow.com/a/25478560
        logging.debug( "    this_fmla : \n'" + this_fmla + "'\n simplifies to :" )
        this_fmla = "(" + str( z3.simplify( eval( this_fmla ) ) ) + ")"
        this_fmla = this_fmla.translate( None, string.whitespace )
        this_fmla = this_fmla.replace( "Or", "z3.Or" )
        this_fmla = this_fmla.replace( "And", "z3.And" )
        this_fmla = this_fmla.replace( "Not", "z3.Not" ) # z3 evals get rid of the z3 dots.
        logging.debug( "    " + this_fmla )

    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : orik_rgg : " + str( orik_rgg ) )
    logging.debug( "  ORIK RGG TO BOOLEAN FMLA : returning (2) " + this_fmla )
    logging.debug( "=========================================================end" )
    return this_fmla


  ##################
  #  MAKE LEGIBLE  #
  ##################
  def make_legible( self, lit_str ) :
    logging.debug( "  MAKE SOLN LEGIBLE : lit_str = " + str( lit_str ) )
    lit_str = lit_str.replace( "_RBRKT_", "['" )
    lit_str = lit_str.replace( "_LBRKT_", "']" )
    lit_str = lit_str.replace( "_RPAR_", "(" )
    lit_str = lit_str.replace( "_LPAR_", ")" )
    lit_str = lit_str.replace( "_COMMA_", "','" )
    return lit_str


#########
#  EOF  #
#########
