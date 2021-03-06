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
        entry2 = ch.getCompleteEntity(ch2)

        exact = []
        children = []
        parents = []
        returnValue = {
            'id': s1.getId(),
            'chebi_name': entry.chebiAsciiName,
            'exact': exact,
            'children': children,
            'parents': parents
        }


        if ch1 == ch2:
            exact.append({'id': s2.getId()})
            return returnValue

        if (hasattr(entry, 'OntologyChildren')):
            if hasattr(entry2, 'OntologyParents'):
                entity2_parents = dict((x['chebiId'], x) for x in entry2.OntologyParents if x['type'] == 'is a')
            else:
                entity2_parents = {}
            for child in entry.OntologyChildren:
                if child['chebiId'] == ch2 or (child['type'] == 'is a' and child['chebiId'] in entity2_parents):
                    children.append({
                        'id': s2.getId(),
                        'data': child
                        })

        if (hasattr(entry, 'OntologyParents')):
            if hasattr(entry2, 'OntologyChildren'):
                entity2_children = dict((x['chebiId'], x) for x in entry2.OntologyChildren if x['type'] == 'is a')
            else:
                entity2_children = {}
            for parent in entry.OntologyParents:
                if parent['chebiId'] == ch2 or (parent['type'] == 'is a' and parent['chebiId'] in entity2_children):
                    parents.append({
                        'id': s2.getId(),
                        'data': parent
                        })

        return returnValue
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


def get_biomodel_id(sbml):
    '''Returns the biomodel ID read from model annotation
    '''
    import libsbml
    import re
    if not isinstance(sbml, libsbml.SBMLDocument):
        raise Exception('Need to call with libsbml.Document instance')

    uris = getResourceUris(sbml.model)
    matches = [re.match('.*biomodels\.db/(BIOMD.*)', uri, re.IGNORECASE)
               for uri in uris]
    matches = [match for match in matches if match]
    if not matches:
        matches = [re.match('.*biomodels\.db/(MODEL.*)', uri, re.IGNORECASE)
                   for uri in uris]
        matches = [match for match in matches if match]
    if matches:
        return matches[0].group(1)
