def append_annotations(doc, annotations):
    '''Append annotations to an SBML document

    :param doc: the SBML document object
    :param annotations: a dictionary containing the element annotations in
    this form:

    annotations = {
        'glu': (libsbml.BQB_IS, 'http://identifiers.org/chebi/CHEBI:17234'),
        'g6p': (libsbml.BQB_IS, 'http://identifiers.org/chebi/CHEBI:17719'),
        'J1': (libsbml.BQB_IS, 'http://identifiers.org/kegg.reaction/R00299')
    }
    '''
    import libsbml
    for elId, annot in annotations.items():
        cv = libsbml.CVTerm()
        cv.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
        cv.setBiologicalQualifierType(annot[0])
        cv.addResource(annot[1])
        el = doc.getElementBySId(elId)
        if not el.getMetaId():
            el.setMetaId(elId + '_meta')  # Add default meta ID
        el.addCVTerm(cv)
    return doc
