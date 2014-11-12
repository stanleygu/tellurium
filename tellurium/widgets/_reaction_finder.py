class ReactionFinder():
    def __init__(self):
        import bioservices
        import IPython.html.widgets as w
        from IPython.display import display
        self.bm = bioservices.BioModels()
        self.ch = bioservices.ChEBI()
        self.kegg = bioservices.KEGG()

        self.widgets = {
            'ontologySelect': w.DropdownWidget(
                description='Ontology:',
                values=['ChEBI', 'GO']),
            'searchTerm': w.TextWidget(description='Search Term:'),
            'searchButton': w.ButtonWidget(description='Search'),
            'ontologyResults': w.SelectWidget(description='Matching Terms'),
            'reactionResults': w.SelectWidget(description='Matched Reactions:'),
            'selectedReaction': w.ContainerWidget(children=[
                w.ImageWidget(),
                w.TextareaWidget(description='Antimony:'),
                w.TextareaWidget(description='Import Code:')
            ])
        }
        self.container = w.ContainerWidget(children=[
            self.widgets['ontologySelect'],
            self.widgets['searchTerm'],
            self.widgets['searchButton'],
            self.widgets['ontologyResults'],
            self.widgets['reactionResults'],
            self.widgets['selectedReaction']
        ])

        self.popup = w.PopupWidget(description="Search Antimony \
                                   Reactions from BioModels",
                                   children=[self.container])

        # Behavior
        self.widgets['searchTerm'].on_submit(self.search_ontology)
        self.widgets['searchButton'].on_click(self.search_ontology)
        self.widgets['ontologyResults'].on_trait_change(
            self.create_parts, 'value')
        self.widgets['reactionResults'].on_trait_change(
            self.selected_part, 'value')

        display(self.popup)
        self.set_visible(2)

    def set_visible(self, ind):
        from IPython.display import clear_output
        clear_output()
        for i, widget in enumerate(self.container.children):
            if i <= ind:
                widget.visible = True
            else:
                widget.visible = False

    def search_ontology(self, b):
        if self.widgets['ontologySelect'].value == 'ChEBI':
            results = self.ch.getLiteEntity(self.widgets['searchTerm'].value)
            choices = [result['chebiId'] for result in results]
            choiceText = ['%s (%s)' % (
                result['chebiId'], result['chebiAsciiName'])
                for result in results]
            values = {}
            for choice, text in zip(choices, choiceText):
                values[text] = choice
            self.widgets['ontologyResults'].values = values

    def create_parts(self):
        import libsbml
        from tellurium.analysis import _annotations
        self.set_visible(3)
        uri_id = self.widgets['ontologyResults'].value
        if self.widgets['ontologySelect'].value == 'ChEBI':
            matched_ids = self.bm.getModelsIdByChEBIId(uri_id)
        elif self.widgets['ontologySelect'].value == 'GO':
            matched_ids = self.bm.getModelsIdByGO(uri_id)
        else:
            raise Exception('No ontology selected')
        if not matched_ids:
            print 'No biomodels containing %s' % uri_id
            return

        self.matched_sbml = [libsbml.readSBMLFromString(
            self.bm.getModelSBMLById(id).encode('utf-8'))
            for id in matched_ids]
        self.matched_sbml_lookup = dict(zip(matched_ids, self.matched_sbml))
        self.matched_reactions = [_annotations.matching_reactions(sbml, uri_id)
                                  for sbml in self.matched_sbml]
        values = {}
        for r in sum(self.matched_reactions, []):
            msg = '%s: %s' % (
                _annotations.get_biomodel_id(r.model.getSBMLDocument()),
                r.__str__())
            values[msg] = r

        self.widgets['reactionResults'].values = values

    def selected_part(self):
        from tellurium.visualization import SBMLDiagram
        from tellurium.analysis import _annotations, make_submodel
        import tellurium as te

        self.set_visible(5)
        r = self.widgets['reactionResults'].value
        biomodel_id = _annotations.get_biomodel_id(r.model.getSBMLDocument())
        self.sbml = self.matched_sbml_lookup[biomodel_id]
        self.submodel = make_submodel(r)
        antimony = te.sbmlToAntimony(self.submodel.toSBML())
        self.widgets['selectedReaction'].children[1].value = antimony

        # Draw diagram
        diagram = SBMLDiagram(self.submodel, reactions={
            'shape': 'box'
        })
        img = diagram.draw(layout='dot')
        self.widgets['selectedReaction'].children[0].value = img.data

        # Modular import code snippet
        self.widgets['selectedReaction'].children[2].value = '''!pip install git+https://github.com/biomodels/%s.git > /dev/null
import %s as m

import tellurium as te
from tellurium.analysis import make_submodel
r = m.sbml.model.getReaction('%s')
submodel = make_submodel(r)
antimony = te.sbmlToAntimony(submodel.toSBML())
print antimony
''' % (biomodel_id, biomodel_id, r.getId())
