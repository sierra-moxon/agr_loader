class Indicies(object):

    def __init__(self, graph):
        self.graph = graph

    def create_indices(self):
        session = self.graph.session()

        session.run("CREATE INDEX ON :Gene(primaryKey)")
        session.run("CREATE INDEX ON :GOTerm(primaryKey)")
        session.run("CREATE INDEX ON :Genotype(primaryKey)")
        session.run("CREATE INDEX ON :SOTerm(primaryKey)")
        session.run("CREATE INDEX ON :Ontology(primaryKey)")
        session.run("CREATE INDEX ON :DOTerm(primaryKey)")
        session.run("CREATE INDEX ON :DOTerm(oid)")
        session.run("CREATE INDEX ON :GOTerm(oid)")
        session.run("CREATE INDEX ON :Publication(primaryKey)")
        session.run("CREATE INDEX ON :EvidenceCode(primaryKey)")
        session.run("CREATE INDEX ON :Transgene(primaryKey)")
        session.run("CREATE INDEX ON :Fish(primaryKey)")
        session.run("CREATE INDEX ON :DiseaseObject(primaryKey)")
        session.run("CREATE INDEX ON :EnvironmentCondition(primaryKey)")
        session.run("CREATE INDEX ON :Environment(primaryKey)")
        session.run("CREATE INDEX ON :Species(primaryKey)")
        session.run("CREATE INDEX ON :Annotation(primaryKey)")
        session.run("CREATE INDEX ON :Entity(primaryKey)")
        session.run("CREATE INDEX ON :Synonym(primaryKey)")
        session.run("CREATE INDEX ON :Identifier(primaryKey)")
        session.run("CREATE INDEX ON :Association(primaryKey)")
        session.run("CREATE INDEX ON :CrossReference(primaryKey)")
        session.run("CREATE INDEX ON :CrossReference(globalCrossRefId)")
        session.run("CREATE INDEX ON :CrossReference(localId)")
        session.run("CREATE INDEX ON :CrossReference(crossRefType)")
        session.run("CREATE INDEX on :CrossReferenceMetaData(primaryKey)")
        session.run("CREATE INDEX ON :OrthologyGeneJoin(primaryKey)")
        session.run("CREATE INDEX ON :GOGeneJoin(primaryKey)")
        session.run("CREATE INDEX ON :SecondaryId(primaryKey)")
        session.run("CREATE INDEX ON :Chromosome(primaryKey)")
        session.run("CREATE INDEX ON :OrthoAlgorithm (name)")
        session.run("CREATE INDEX ON :Gene(modGlobalId)")
        session.run("CREATE INDEX ON :Gene(localId)")
        session.run("CREATE INDEX ON :Load(primaryKey)")
        session.run("CREATE INDEX ON :Feature(primaryKey)")
        session.run("CREATE INDEX ON :MITerm(primaryKey)")
        session.run("CREATE INDEX ON :Phenotype(primaryKey)")
        session.run("CREATE INDEX ON :PhenotypeEntityJoin(primaryKey)")

        #session.run("CREATE CONSTRAINT ON (g:Gene) ASSERT g.primaryKey IS UNIQUE;")

        #session.run("CREATE CONSTRAINT ON (n:Gene) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:GOTerm) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Genotype) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:SOTerm) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Ontology) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:DOTerm) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Publication) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:EvidenceCode) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Allele) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Transgene) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Fish) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:DiseaseObject) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:EnvironmentCondition) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Environment) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Species) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Annotation) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Entity) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Synonym) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Identifier) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:ExternalId) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Association) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:CrossReference) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:SecondaryId) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:Chromosome) ASSERT n.primaryKey IS UNIQUE")
        #session.run("CREATE CONSTRAINT ON (n:OrthoAlgorithm) ASSERT n.name IS UNIQUE")

        session.close()

    # Property constraints require Enterprise Edition. :(
    # def create_constraints(self):
    #     session = self.graph.session()
    #     session.run("CREATE CONSTRAINT ON (g:Gene) ASSERT g.primaryKey IS UNIQUE")
    #     session.run("CREATE CONSTRAINT ON (g:Gene) ASSERT exists(g.primaryKey)")

    #     session.run("CREATE CONSTRAINT ON (go:GOTerm) ASSERT go.primaryKey IS UNIQUE")
    #     session.run("CREATE CONSTRAINT ON (go:GOTerm) ASSERT exists(go.primaryKey)")
    #     session.close()
