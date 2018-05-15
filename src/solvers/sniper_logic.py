import collections
import logging
import sys
import re


#########################
#  STILL IDEM OR EXPRS  #
#########################
def still_idem_or_exprs( fmla ) :
  logging.debug( "  STILL IDEM OR EXPRS : input fmla = " + fmla )
  p_or_exprs = re.compile( "[a-zA-Z0-9_]+[\|]{1}[a-zA-Z0-9_]+" )
  idem_or_exprs = [ x for x in p_or_exprs.findall( fmla ) if x.split("|")[0] == x.split("|")[1] ]
  if len( idem_or_exprs ) > 0 :
    logging.debug( "  STILL IDEM OR EXPRS : returning True" )
    return True
  else :
    logging.debug( "  STILL IDEM OR EXPRS : returning False" )
    return False


##########################
#  STILL IDEM AND EXPRS  #
##########################
def still_idem_and_exprs( fmla ) :
  logging.debug( "  STILL IDEM AND EXPRS : input fmla = " + fmla )
  p_and_exprs = re.compile( "[a-zA-Z0-9_]+[\&]{1}[a-zA-Z0-9_]+" )
  idem_and_exprs = [ x for x in p_and_exprs.findall( fmla ) if x.split("&")[0] == x.split("&")[1] ]
  if len( idem_and_exprs ) > 0 :
    logging.debug( "  STILL IDEM AND EXPRS : returning True" )
    return True
  else :
    logging.debug( "  STILL IDEM AND EXPRS : returning False" )
    return False


##################
#  GET IDEM ORS  #
##################
def get_idem_ors( p_or, fmla ) :
  idem_ors = []
  all_ors  = p_or.findall( fmla )
  for or_expr in all_ors :
    logging.debug( "  GET IDEM ORS : " + or_expr )
    lits = or_expr.split( "|" )
    if lits[0] == lits[1] :
      idem_ors.append( or_expr )
  logging.debug( "  GET IDEM ORS : returning idem_ors = " + str( idem_ors ) )
  return idem_ors


###################
#  GET IDEM ANDS  #
###################
def get_idem_ands( p_and, fmla ) :
  idem_ands = []
  all_ands  = p_and.findall( fmla )
  for and_expr in all_ands :
    logging.debug( "  GET IDEM ANDS : " + and_expr )
    lits = and_expr.split( "&" )
    if lits[0] == lits[1] :
      idem_ands.append( and_expr )
  logging.debug( "  GET IDEM ANDS : returning idem_ands = " + str( idem_ands ) )
  return idem_ands


#####################
#  CONSERVE PARENS  #
#####################
def conserve_parens( fmla ) :

  logging.debug( "  CONSERVE PARENS : input fmla = " + fmla )

  # grab all seqs of alphanumeric chars between 
  # parens and include parens in grab.
  p = re.compile( "\(\w+\)" )
  parend_lits = list( set( p.findall( fmla ) ) ) # remove duplicates
  logging.debug( "  CONSERVE PARENS : parend_lits = " + str( parend_lits ) )

  # perform paren removals
  if len( parend_lits ) > 0 :
    for plit in parend_lits :
      free_lit = plit[1:-1]
      fmla = fmla.replace( plit, free_lit )

  logging.debug( "  CONSERVE PARENS : output fmla = " + fmla )
  return fmla


#######################
#  DO IDEMPOTENT LAW  #
#######################
# driver
def do_idempotent_law( fmla ) :
  fmla = conserve_parens( fmla )
  while still_idem_or_exprs( fmla ) or still_idem_and_exprs( fmla ) :
    fmla = conserve_parens( fmla )
    fmla = do_idempotent_law_helper( fmla )
    fmla = conserve_parens( fmla )
  return fmla


##############################
#  DO IDEMPOTENT LAW HELPER  #
##############################
def do_idempotent_law_helper( fmla ) :

  logging.debug( "  DO IDEMPOTENT LAW HELPER : input fmla = " + fmla )

  # grab all seqs of alphanumeric chars between
  # parens and separated by |. include parens in grab.
  p_or = re.compile( "[a-zA-Z0-9_]+[\|]{1}[a-zA-Z0-9_]+" )

  # grab idempotent exprs
  idem_ors = get_idem_ors( p_or, fmla )

  # perform idempotent simplification
  if len( idem_ors ) > 0 :
    for or_expr in idem_ors :
      logging.debug( "  DO IDEMPOTENT LAW HELPER : or_expr = " + or_expr )
      free_lit = or_expr.split( "|" )[0]
      logging.debug( "  DO IDEMPOTENT LAW HELPER : free_lit = " + free_lit )
      fmla = fmla.replace( or_expr, free_lit )

  # grab all seqs of alphanumeric chars between
  # parens and separated by &. include parens in grab.
  p_and = re.compile( "[a-zA-Z0-9_]+[\&]{1}[a-zA-Z0-9_]+" )

  # grab idempotent exprs
  idem_ands = get_idem_ands( p_and, fmla )

  # perform idempotent simplification
  if len( idem_ands ) > 0 :
    for and_expr in idem_ands :
      logging.debug( "  DO IDEMPOTENT LAW HELPER : and_expr = " + and_expr )
      free_lit = and_expr.split( "&" )[0]
      logging.debug( "  DO IDEMPOTENT LAW HELPER : free_lit = " + free_lit )
      fmla = fmla.replace( and_expr, free_lit )

  logging.debug( "  DO IDEMPOTENT LAW HELPER : output fmla = " + fmla )
  return fmla


#######################
#  DO ABSORPTION LAW  #
#######################
# driver
def do_absorption_law( fmla ) :

  # define absorption law
  expr_1   = "[a-zA-Z0-9_]+[\|]{1}[(][a-zA-Z0-9_]+[\&][a-zA-Z0-9_]+[)]"
  expr_2   = "[(][a-zA-Z0-9_]+[\&][a-zA-Z0-9_]+[)][\|]{1}[a-zA-Z0-9_]+"
  expr_3   = "[a-zA-Z0-9_]+[\&]{1}[(][a-zA-Z0-9_]+[\|][a-zA-Z0-9_]+[)]"
  expr_4   = "[(][a-zA-Z0-9_]+[\|][a-zA-Z0-9_]+[)][\&]{1}[a-zA-Z0-9_]+"
  p_absorp = re.compile( expr_1 + "|" + expr_2 + "|" + expr_3 + "|" + expr_4 )

  fmla = conserve_parens( fmla )
  while still_absorption_exprs( fmla ) :
    fmla = conserve_parens( fmla )
    fmla = do_absorption_law_helper( p_absorp, fmla )
    fmla = conserve_parens( fmla )
  return fmla


############################
#  STILL ABSORPTION EXPRS  #
############################
def still_absorption_exprs( fmla ) :

  # define absorption law to make this callable from PYCOSAT
  expr_1   = "[a-zA-Z0-9_]+[\|]{1}[(][a-zA-Z0-9_]+[\&][a-zA-Z0-9_]+[)]"
  expr_2   = "[(][a-zA-Z0-9_]+[\&][a-zA-Z0-9_]+[)][\|]{1}[a-zA-Z0-9_]+"
  expr_3   = "[a-zA-Z0-9_]+[\&]{1}[(][a-zA-Z0-9_]+[\|][a-zA-Z0-9_]+[)]"
  expr_4   = "[(][a-zA-Z0-9_]+[\|][a-zA-Z0-9_]+[)][\&]{1}[a-zA-Z0-9_]+"
  p_absorp = re.compile( expr_1 + "|" + expr_2 + "|" + expr_3 + "|" + expr_4 )

  if len( get_absorption_exprs( p_absorp, fmla ) ) > 0 :
    return True
  else :
    return False


##############################
#  DO ABSORPTION LAW HELPER  #
##############################
def do_absorption_law_helper( p_absorp, fmla ) :
  logging.debug( "  DO ABSORPTION LAW HELPER : input fmla = " + fmla )

  absorption_exprs = get_absorption_exprs( p_absorp, fmla )

  if len( absorption_exprs ) > 0 :
    fmla = do_absorption_substitution( absorption_exprs, fmla )

  logging.debug( "  DO ABSORPTION LAW HELPER : output fmla = " + fmla )
  return fmla


################################
#  DO ABSORPTION SUBSTITUTION  #
################################
def do_absorption_substitution( exprs, fmla ) :
  for expr in exprs :
    if "|(" in expr :
      lit = expr.split( "|(" )[0]
    elif ")|" in expr :
      lit = expr.split( ")|" )[1]
    elif "&(" in expr :
      lit = expr.split( "&(" )[0]
    elif ")&" in expr :
      lit = expr.split( ")&" )[1]
    else :
      raise Exception( "something isn't right. aborting..." )
    fmla = fmla.replace( expr, lit )
    return fmla


##########################
#  GET ABSORPTION EXPRS  #
##########################
def get_absorption_exprs( p, fmla ) :

  valid_exprs = []
  all_exprs   = p.findall( fmla )

  for expr in all_exprs :

    # make sure this is a valid expression wrt operators
    # A | ( A | B ) is invalid.
    if not expr.count( "|" ) == 1 or not expr.count( "&" ) == 1 :
      logging.debug( "skipping 1" )
      continue

    else :
      # A | ( A & A ) is invalid.
      expr_cp = expr.replace( "(", "" )
      expr_cp = expr_cp.replace( ")", "" )
      expr_cp = expr_cp.replace( "|", "-" )
      expr_cp = expr_cp.replace( "&", "-" )
      expr_cp = expr_cp.split( "-" )
      expr_counter = collections.Counter( expr_cp )
      logging.debug( "expr_counter = " + str( expr_counter ) )
      if not len( expr_counter ) == 2 :
        logging.debug( "skipping 2" )
        continue

      else :
        if "|(" in expr or ")|" in expr :
          lhs = expr.split( "|" )[0]
          rhs = expr.split( "|" )[1]
          if "&" in lhs :
            lhs = lhs.split( "&" )
            if not len( lhs ) == 2 :
              logging.debug( "skipping 3" )
              continue
            # B|(A&A) is invalid.
            elif lhs[0] == lhs[1] :
              logging.debug( "skipping 4" )
              continue
            else :
              valid_exprs.append( expr )
          elif "&" in rhs :
            rhs = rhs.split( "&" )
            if not len( rhs ) == 2 :
              logging.debug( "skipping 5" )
              continue
            elif rhs[0] == rhs[1] :
              logging.debug( "skipping 6" )
              continue
            else :
              valid_exprs.append( expr )
          else :
            logging.debug( "skipping 7" )
            continue
        elif "&(" in expr or ")&" in expr :
          lhs = expr.split( "&" )[0]
          rhs = expr.split( "&" )[1]
          if "|" in lhs :
            lhs = lhs.split( "|" )
            if not len( lhs ) == 2 :
              logging.debug( "skipping 8" )
              continue
            # B&(A|A) is invalid.
            elif lhs[0] == lhs[1] :
              logging.debug( "skipping 9" )
              continue
            else :
              valid_exprs.append( expr )
          elif "|" in rhs :
            rhs = rhs.split( "|" )
            if not len( rhs ) == 2 :
              logging.debug( "skipping 10" )
              continue
            elif rhs[0] == rhs[1] :
              logging.debug( "skipping 11" )
              continue
            else :
              valid_exprs.append( expr )
          else :
            logging.debug( "skipping 12" )
            continue

  logging.debug( "valid_exprs = " + str( valid_exprs ) )
  return valid_exprs


#########
#  EOF  #
#########
