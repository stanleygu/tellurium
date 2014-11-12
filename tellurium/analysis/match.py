import _annotations


def getMatchingSpecies(m1, m2, logging=False):
    '''
    Returns a list of species with matching annotations URIs
    '''
    import libsbml
    if not isinstance(m1, libsbml.Model) or not isinstance(m2, libsbml.Model):
        raise Exception('Need to call with two libsbml.Model instances')

    matches = []
    for s1 in m1.species:
        for s2 in m2.species:
            match = _annotations.matchSpeciesChebi(s1, s2, logging=logging)
            if match:
                if len(match['exact']) or \
                        len(match['children']) or \
                        len(match['parents']):
                    matches.append(match)
    return matches


def printMatchingSpecies(matches):
    '''Prints the matches from getMatchingSpecies
    '''
    for match in matches:
        if len(match['exact']):
            print '%s exactly matches %s' % (
                match['exact'][0]['id'], match['id'])
        if len(match['parents']):
            print '%s %s %s' % (
                match['parents'][0]['id'],
                match['parents'][0]['data']['type'], match['id'])
        if len(match['children']):
            print '%s %s %s' % (
                match['children'][0]['id'],
                match['children'][0]['data']['type'], match['id'])


def getMatchingReactions(modelOrList, idToMatch):
    '''
    Returns a list of reactions that contains a reactant with the id to match
    '''
    import libsbml
    if isinstance(modelOrList, libsbml.Model):
        reactions = modelOrList.reactions
    else:
        reactions = modelOrList
    matches = []
    for r in reactions:
        for reactant in r.reactants:
            if reactant.getSpecies() == idToMatch:
                matches.append(r)
        for reactant in r.products:
            if reactant.getSpecies() == idToMatch:
                matches.append(r)
        for modifier in r.modifiers:
            if modifier.getSpecies() == idToMatch:
                matches.append(r)
    return matches


def getAllReactionParameters(r):
    '''
    Find all reactions
    '''
    # list to hold found parameters
    params = []
    # initialize frontier to search
    frontier = []
    for i in range(r.kinetic_law.math.getNumChildren()):
        frontier.append(r.kinetic_law.math.getChild(i))
    while len(frontier) > 0:
        node = frontier.pop()

        for i in range(node.getNumChildren()):
            frontier.append(node.getChild(i))

        if node.isName() and r.model.getParameter(node.getName()):
            params.append(r.model.getParameter(node.getName()))

    return params


def getAllReactionFunctions(r):
    '''Find all functions used in a reaction kinetic law
    '''
    # list to hold found functions
    functions = []
    # initialize frontier to search
    frontier = []
    for i in range(r.kinetic_law.math.getNumChildren()):
        frontier.append(r.kinetic_law.math.getChild(i))
    while len(frontier) > 0:
        node = frontier.pop()
        for i in range(node.getNumChildren()):
            frontier.append(node.getChild(i))

        if node.isFunction() and r.model.getFunctionDefinition(node.getName()):
            functions.append(r.model.getFunctionDefinition(node.getName()))

    return functions


def make_submodel(r):
    '''Create a submodel from a reaction
    '''
    import libsbml
    doc = r.getSBMLDocument()
    newDoc = libsbml.SBMLDocument(doc.getLevel(), doc.getVersion())
    newMod = newDoc.createModel()
    newMod.setId(r.model.getId() + '_' + r.getId())

    # Holding elements that will need to be cloned
    species = set()
    compartments = set()
    parameters = set()
    functions = set()
    units = set()

    for reactant in r.reactants:
        s = r.model.getSpecies(reactant.getSpecies())
        species.add(s)
        compartments.add(r.model.getCompartment(s.getCompartment()))
    for product in r.products:
        s = r.model.getSpecies(product.getSpecies())
        species.add(s)
        compartments.add(r.model.getCompartment(s.getCompartment()))
    for modifier in r.modifiers:
        s = r.model.getSpecies(modifier.getSpecies())
        species.add(s)
        compartments.add(r.model.getCompartment(s.getCompartment()))
    for p in getAllReactionParameters(r):
        parameters.add(p)
        if p.units:
            unit_def = r.model.getUnitDefinition(p.units)
            if isinstance(unit_def, libsbml.UnitDefinition):
                units.add(unit_def)
    for function in getAllReactionFunctions(r):
        functions.add(function)
    for p in r.kinetic_law.parameters:
        if p.units:
            unit_def = r.model.getUnitDefinition(p.units)
            if isinstance(unit_def, libsbml.UnitDefinition):
                units.add(unit_def)
    newMod.addReaction(r.clone())

    # Clone additional elements
    for s in species:
        newMod.addSpecies(s.clone())

    for p in parameters:
        newMod.addParameter(p.clone())
    while len(compartments):
        c = compartments.pop()
        newMod.addCompartment(c.clone())
        if c.getOutside():
            compartments.add(
                r.model.getCompartment(c.getOutside())
            )
    for u in units:
        newMod.addUnitDefinition(u.clone())
    for f in functions:
        newMod.addFunctionDefinition(f.clone())

    return newDoc
