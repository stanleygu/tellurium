'''
Functions for handling ontology annotations
'''


def getResourceUris(item):
                    # qualifierType=libsbml.BIOLOGICAL_QUALIFIER,
                    # biologicalQualifierType=libsbml.BQB_IS):
    '''
    Returns a list of all resource URIs for the given element
    '''
    uris = []
    for i in range(item.getNumCVTerms()):
        term = item.getCVTerm(i)
        # if (term.getQualifierType() == qualifierType
        #     and term.getBiologicalQualifierType() == biologicalQualifierType):
        for j in range(term.getNumResources()):
            uris.append(term.getResourceURI(j))
    return uris


def getChebiId(item):
    '''Returns the ChEBI ID from element
    '''
    import re
    uris = getResourceUris(item)
    chebiMatches = (re.match('.*(CHEBI:\d+)', uri) for uri in uris)
    chebiIds = [match.group(1) for match in chebiMatches if match]
    if len(chebiIds) > 0:
        return chebiIds[0]
    else:
        return None


def matchSpeciesChebi(s1, s2, logging=False):
    import bioservices
    ch = bioservices.ChEBI()

    ch1 = getChebiId(s1)
    ch2 = getChebiId(s2)

    if not ch1 or not ch2:
        return None

    if logging:
        print 'Comparing %s (%s) with %s (%s)' % (
            s1.getId(), ch1, s2.getId(), ch2)

    try:
        entry = ch.getCompleteEntity(ch1)

        exact = []
        if ch1 == ch2:
            exact.append({'id': s2.getId()})

        children = []
        if (hasattr(entry, 'OntologyChildren')):
            for child in entry.OntologyChildren:
                if child['chebiId'] == ch2:
                    children.append({
                        'id': s2.getId(),
                        'data': child
                        })

        parents = []
        if (hasattr(entry, 'OntologyParents')):
            for parent in entry.OntologyParents:
                if parent['chebiId'] == ch2:
                    parents.append({
                        'id': s2.getId(),
                        'data': parent
                        })

        return {
            'id': s1.getId(),
            'chebi_name': entry.chebiAsciiName,
            'exact': exact,
            'children': children,
            'parents': parents
        }
    except:
        import sys
        print "Unexpected error:", sys.exc_info()[0]
        return None


def matching_reactions(sbml, uri):
    '''Returns list of reactions matching resource URI

    sbml - SBML document to search for reactions
    uri - String of resource URI to match
    '''
    import libsbml

    if not isinstance(sbml, libsbml.SBMLDocument):
        raise Exception('Need to call with libsbml.Document instance')

    matches = []

    for reaction in sbml.model.reactions:
        reactants = [sbml.model.getSpecies(reactant.getSpecies())
                     for reactant in reaction.reactants]
        products = [sbml.model.getSpecies(product.getSpecies())
                    for product in reaction.products]
        modifiers = [sbml.model.getSpecies(modifier.getSpecies())
                     for modifier in reaction.modifiers]
        all_uris = []
        for el in [reaction] + reactants + products + modifiers:
            all_uris += getResourceUris(el)

        if any(u for u in all_uris if uri in u):
            matches.append(reaction)
    return matches
