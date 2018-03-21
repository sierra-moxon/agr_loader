from .mod import MOD

class FlyBase(MOD):

    def __init__(self):
        self.species = "Drosophila melanogaster"
        self.loadFile = "FB_1.0.0.0_2.tar.gz"
        self.bgiName = "/FB_1.0.0.0_BGI.json"
        self.diseaseName = "/FB_1.0.0.0_disease.json"
        self.alleleName = "/FB_1.0.0.0_feature.json"
        self.geneAssociationFile = "FB_1.0.0.0_GFF.gff"
        self.identifierPrefix = "FB:"

    def load_genes(self, batch_size, testObject, graph):
        data = MOD.load_genes_mod(self, batch_size, testObject, self.bgiName, self.loadFile, graph)
        return data

    @staticmethod
    def gene_href(gene_id):
        return "http://flybase.org/reports/" + gene_id + ".html"

    @staticmethod
    def get_organism_names():
        return ["Drosophila melanogaster", "D. melanogaster", "DROME"]

    def extract_go_annots(self, testObject):
        go_annot_list = MOD.extract_go_annots_mod(self, self.geneAssociationFile, self.species, self.identifierPrefix, testObject)
        return go_annot_list

    def load_disease_gene_objects(self, batch_size, testObject):
        data = MOD.load_disease_gene_objects_mod(self, batch_size, testObject, self.diseaseName, self.loadFile)
        return data

    def load_disease_allele_objects(self, batch_size, testObject, graph):
        data = MOD.load_disease_allele_objects_mod(self, batch_size, testObject, self.diseaseName, self.loadFile, graph)
        return data

    def load_allele_objects(self, batch_size, testObject):
        data = MOD.load_allele_objects_mod(self, batch_size, testObject, self.alleleName, self.loadFile)
        return data
