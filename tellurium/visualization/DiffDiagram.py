from collections import namedtuple

class DiffDiagram():
    '''
    Create a network diagram from a sbml model.
    '''

    def __init__(self, sbml_to_compare):
        '''
        sbml_to_compare -- list of two SBML strings, libsbml.SBMLDocument objects, or
        libsbml.Model objects, to compare
        '''
        import pygraphviz as pgv
        import libsbml
        from tellurium.analysis import getMatchingSpecies, getMatchingReactions

        # List of the two sbml documents to create diff
        self.doc = []
        # List of two sets, containing the IDs of overlapping species
        self.matches = [set(), set()]
        # The pygraphviz graph object
        self.G = pgv.AGraph(strict=False, directed=True)


        for sbml in sbml_to_compare:
            if isinstance(sbml, basestring):
                self.doc.append(libsbml.readSBMLFromString(sbml))
            elif isinstance(sbml, libsbml.SBMLDocument):
                self.doc.append(sbml)
            elif isinstance(sbml, libsbml.Model):
                self.doc.append(sbml.getSBMLDocument())
            else:
                raise Exception('SBML Input is not valid')

        matching_species = getMatchingSpecies(self.doc[0].model, self.doc[1].model)

        # Create set of overlapping species IDs
        for entry in matching_species:
            self.matches[0].add(entry['id'])
            for sub_entry in entry['children']:
                self.matches[1].add(sub_entry['id'])
            for sub_entry in entry['parents']:
                self.matches[1].add(sub_entry['id'])

        first_color = 'blue'
        second_color = 'red'
        match_color = 'green'
        for s in self.doc[0].model.species:
            if s.getId() in self.matches[0]:
                label = s.getName() + ' ()'
            elif s.getName():
                label = s.getName()
            else:
                label = s.getId()

            if s.getId() in self.matches[0]:
                color = match_color
            else:
                color = first_color
            self.G.add_node(s.getId(), label=label, color=color)
        for r in self.doc[0].model.reactions:
            if r.getName():
                label = r.getName()
            else:
                label = r.getId()
            self.G.add_node(r.getId(), label=label, shape='box', color=first_color)
            for s in r.reactants:
                self.G.add_edge(s.getSpecies(), r.getId(), arrowhead='none', color=first_color)
            for s in r.products:
                self.G.add_edge(r.getId(), s.getSpecies(), color=first_color)
            for s in r.modifiers:
                self.G.add_edge(s.getSpecies(), r.getId(), arrowhead='odot', color=first_color)




        # for i, s in enumerate(self.model.species):
        #     if s.getName():
        #         label = s.getName()
        #     else:
        #         label = s.getId()
        #     self.G.add_node(s.getId(), label=label, **species)
        # for i, r in enumerate(self.model.reactions):
        #     if r.getName():
        #         label = r.getName()
        #     else:
        #         label = r.getId()
        #     self.G.add_node(r.getId(), label=label, **reactions)
        #     for s in r.reactants:
        #         self.G.add_edge(s.getSpecies(), r.getId(), **reactants)
        #     for s in r.products:
        #         self.G.add_edge(r.getId(), s.getSpecies(), **products)
        #     for s in r.modifiers:
        #         self.G.add_edge(s.getSpecies(), r.getId(), **modifiers)

    def draw(self,
             layout='neato'):
        '''
        Draw the graph

        Optional layout=['neato'|'dot'|'twopi'|'circo'|'fdp'|'nop']
        will use specified graphviz layout method.
        '''
        import tempfile
        from IPython.display import Image
        import os

        f = tempfile.NamedTemporaryFile()
        fname = f.name + '.png'
        self.G.layout(prog=layout)
        self.G.draw(fname)

        i = Image(filename=fname)
        os.remove(fname)
        return i
