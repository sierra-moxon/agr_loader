import logging
import os
import datetime

from collections import defaultdict

import boto3
from etl import ETL
from etl.helpers import Neo4jHelper
from genedescriptions.config_parser import GenedescConfigParser
from genedescriptions.descriptions_writer import DescriptionsWriter
from genedescriptions.gene_description import GeneDescription
from ontobio import AssociationSetFactory, OntologyFactory
from transactors import CSVTransactor, Neo4jTransactor
from genedescriptions.data_manager import DataManager
from genedescriptions.commons import DataType, Gene
from genedescriptions.precanned_modules import set_gene_ontology_module, set_disease_module, \
    set_alliance_human_orthology_module
from common import ContextInfo
from data_manager import DataFileManager

logger = logging.getLogger(__name__)


class GeneDescriptionsETL(ETL):

    GeneDescriptionsQuery = """

        USING PERIODIC COMMIT %s
        LOAD CSV WITH HEADERS FROM \'file:///%s\' AS row
        
        MATCH (o:Gene) where o.primaryKey = row.genePrimaryKey 
        SET o.automatedGeneSynopsis = row.geneDescription
        """

    GetAllGenesQuery = """
        
        MATCH (g:Gene) where g.dataProvider = {parameter} AND NOT g.primaryKey CONTAINS "HGNC:"
        RETURN g.primaryKey, g.symbol
        """

    GetAllGenesHumanQuery = """

        MATCH (g:Gene) where g.dataProvider = {parameter} AND g.primaryKey CONTAINS "HGNC:"
        RETURN g.primaryKey, g.symbol
        """

    GetGOTermsPairs = """

        MATCH (term1:GOTerm:Ontology)-[r:IS_A|PART_OF]->(term2) 
        RETURN term1.primaryKey, term1.name, term1.type, term2.primaryKey, term2.name, term2.type, type(r) AS rel_type
        """

    GetGeneDiseaseAnnotQuery = """
    
        MATCH (d:DOTerm:Ontology)-[r:IS_MARKER_FOR|IS_IMPLICATED_IN|IS_MODEL_OF]-(g:Gene)-[:ASSOCIATION]->
        (dga:Association:DiseaseEntityJoin)-[:ASSOCIATION]->(d) 
        WHERE g.dataProvider = {parameter}
        MATCH (dga)-[:EVIDENCE]->(pec:PublicationEvidenceCodeJoin)-[:ASSOCIATION]-(e:EvidenceCode)
        RETURN DISTINCT g.primaryKey AS geneId, g.symbol AS geneSymbol, d.primaryKey AS DOId, e.primaryKey AS ECode, 
            type(r) AS relType
        """

    GetFeatureDiseaseAnnotQuery = """

        MATCH (d:DOTerm:Ontology)-[r:IS_MARKER_FOR|IS_IMPLICATED_IN|IS_MODEL_OF]-(f)-[:ASSOCIATION]->
        (dga:Association:DiseaseEntityJoin)-[:ASSOCIATION]->(d)
        WHERE f.dataProvider = {parameter}
        MATCH (f)<-[:IS_ALLELE_OF]->(g:Gene)
        MATCH (dga)-[:EVIDENCE]->(pec:PublicationEvidenceCodeJoin)-[:ASSOCIATION]-(e:EvidenceCode)
        RETURN DISTINCT g.primaryKey AS geneId, g.symbol AS geneSymbol, f.primaryKey as alleleId, d.primaryKey as DOId, 
        e.primaryKey AS ECode, type(r) AS relType
        """

    GetFilteredHumanOrthologsQuery = """
        
        MATCH (g2)<-[orth:ORTHOLOGOUS]-(g:Gene)-[:ASSOCIATION]->(ogj:Association:OrthologyGeneJoin)-[:ASSOCIATION]->
        (g2:Gene)
        WHERE ogj.joinType = 'orthologous' AND g.dataProvider = {parameter} AND g2.taxonId ='NCBITaxon:9606' AND 
        orth.strictFilter = true
        MATCH (ogj)-[:MATCHED]->(oa:OrthoAlgorithm)
        RETURN g.primaryKey AS geneId, g2.primaryKey AS orthoId, g2.symbol AS orthoSymbol, g2.name AS orthoName, 
        oa.name AS algorithm
        """

    GetDiseaseViaOrthologyQuery = """
    
        MATCH (disease:DOTerm:Ontology)-[da:IS_IMPLICATED_IN|:IS_MODEL_OF]-(gene1:Gene)-[o:ORTHOLOGOUS]->(gene2:Gene)
        MATCH (ec:EvidenceCode)-[:EVIDENCE]-(dej:DiseaseEntityJoin)-[:EVIDENCE]->(p:Publication)
        WHERE o.strictFilter = 'True' AND gene1.taxonId ='NCBITaxon:9606' AND da.uuid = dej.primaryKey 
        AND NOT ec.primaryKey IN ["IEA", "ISS", "ISO"] AND gene2.dataProvider = {parameter}
        RETURN DISTINCT gene2.primaryKey AS geneId, gene2.symbol AS geneSymbol, disease.primaryKey AS DOId, 
        p.primaryKey AS publicationId
        """

    def __init__(self, config):
        super().__init__()
        self.data_type_config = config

    def _load_and_process_data(self):
        # create gene descriptions data manager and load common data
        context_info = ContextInfo()
        data_manager = DataFileManager(context_info.config_file_location)
        go_onto_config = data_manager.get_config('GO')
        go_annot_config = data_manager.get_config('GAF')
        do_onto_config = data_manager.get_config('DO')
        go_annot_sub_dict = {sub.get_data_provider(): sub for sub in go_annot_config.get_sub_type_objects()}
        this_dir = os.path.split(__file__)[0]
        gd_config = GenedescConfigParser(os.path.join(this_dir, os.pardir, os.pardir, "gene_descriptions.yml"))
        gd_data_manager = DataManager(do_relations=None, go_relations=["subClassOf", "BFO:0000050"])
        go_onto_path = "file://" + os.path.join(os.getcwd(), go_onto_config.get_single_filepath())
        gd_data_manager.load_ontology_from_file(ontology_type=DataType.GO, ontology_url=go_onto_path, config=gd_config,
                                                ontology_cache_path=os.path.join(os.getcwd(), "tmp", "gd_cache", "go.obo"))
        #gd_data_manager.set_ontology(ontology_type=DataType.GO,
        #                             ontology=GeneDescriptionsETL.get_ontology(data_type=DataType.GO), config=gd_config)
        do_onto_path = "file://" + os.path.join(os.getcwd(), do_onto_config.get_single_filepath())
        gd_data_manager.load_ontology_from_file(ontology_type=DataType.DO, ontology_url=do_onto_path, config=gd_config,
                                                ontology_cache_path=os.path.join(os.getcwd(), "tmp", "gd_cache", "do.obo"))
        # generate descriptions for each MOD
        for prvdr in [sub_type.get_data_provider() for sub_type in self.data_type_config.get_sub_type_objects()]:
            logger.info("Generating gene descriptions for " + prvdr)
            data_provider = prvdr if prvdr != "Human" else "RGD"
            json_desc_writer = DescriptionsWriter()
            go_annot_path = "file://" + os.path.join(os.getcwd(), "tmp", go_annot_sub_dict[prvdr].file_to_download)
            gd_data_manager.load_associations_from_file(
                associations_type=DataType.GO, associations_url=go_annot_path,
                associations_cache_path=os.path.join(os.getcwd(), "tmp", "gd_cache", "go_annot_" + prvdr + ".gaf"),
                config=gd_config)
            key_diseases = defaultdict(set)
            gd_data_manager.set_associations(
                associations_type=DataType.DO, associations=self.get_disease_annotations_from_db(
                    data_provider=data_provider, gd_data_manager=gd_data_manager, key_diseases=key_diseases),
                config=gd_config)
            commit_size = self.data_type_config.get_neo4j_commit_size()
            generators = self.get_generators(prvdr, gd_data_manager, gd_config, key_diseases, json_desc_writer)
            query_list = [
                [GeneDescriptionsETL.GeneDescriptionsQuery, commit_size, "genedescriptions_data_" + prvdr + ".csv"], ]
            query_and_file_list = self.process_query_params(query_list)
            CSVTransactor.save_file_static(generators, query_and_file_list)
            Neo4jTransactor.execute_query_batch(query_and_file_list)
            self.save_descriptions_report_files(data_provider=prvdr, json_desc_writer=json_desc_writer)

    def get_generators(self, data_provider, gd_data_manager, gd_config, key_diseases, json_desc_writer):
        gene_prefix = ""
        if data_provider == "Human":
            return_set = Neo4jHelper.run_single_parameter_query(GeneDescriptionsETL.GetAllGenesHumanQuery, "RGD")
            gene_prefix = "RGD:"
        else:
            return_set = Neo4jHelper.run_single_parameter_query(GeneDescriptionsETL.GetAllGenesQuery, data_provider)
        descriptions = []
        best_orthologs = self.get_best_orthologs_from_db(data_provider=data_provider)
        for record in return_set:
            gene = Gene(id=gene_prefix + record["g.primaryKey"], name=record["g.symbol"], dead=False, pseudo=False)
            gene_desc = GeneDescription(gene_id=record["g.primaryKey"], gene_name=gene.name, add_gene_name=False)
            set_gene_ontology_module(dm=gd_data_manager, conf_parser=gd_config, gene_desc=gene_desc, gene=gene)
            set_disease_module(df=gd_data_manager, conf_parser=gd_config, gene_desc=gene_desc, gene=gene,
                               orthologs_key_diseases=key_diseases[gene.id], human=data_provider == "Human")
            if gene.id in best_orthologs:
                gene_desc.stats.set_best_orthologs = best_orthologs[gene.id][0]
                set_alliance_human_orthology_module(orthologs=best_orthologs[gene.id][0],
                                                    excluded_orthologs=best_orthologs[gene.id][1], gene_desc=gene_desc)
            if len(key_diseases[gene.id]) > 5:
                logger.debug("Gene with more than 5 key diseases: " + gene.id + "\t" + gene.name + "\t" +
                             gene_desc.do_orthology_description + "\t" + ",".join(key_diseases[gene.id]))
            if gene_desc.description:
                descriptions.append({
                    "genePrimaryKey": gene_desc.gene_id,
                    "geneDescription": gene_desc.description
                })
            json_desc_writer.add_gene_desc(gene_desc)
        yield [descriptions]

    @staticmethod
    def get_ontology(data_type: DataType):
        ontology = OntologyFactory().create()
        if data_type == DataType.GO:
            terms_pairs = Neo4jHelper.run_single_parameter_query(GeneDescriptionsETL.GetGOTermsPairs, None)
            for terms_pair in terms_pairs:
                GeneDescriptionsETL.add_neo_term_to_ontobio_ontology_if_not_exists(
                    terms_pair["term1.primaryKey"], terms_pair["term1.name"], terms_pair["term1.type"], ontology)
                GeneDescriptionsETL.add_neo_term_to_ontobio_ontology_if_not_exists(
                    terms_pair["term2.primaryKey"], terms_pair["term2.name"], terms_pair["term2.type"], ontology)
                ontology.add_parent(terms_pair["term1.primaryKey"], terms_pair["term2.primaryKey"],
                                    relation="subClassOf" if terms_pair["rel_type"] == "IS_A" else "BFO:0000050")
        return ontology

    @staticmethod
    def add_neo_term_to_ontobio_ontology_if_not_exists(term_id, term_label, term_type, ontology):
        if not ontology.has_node(term_id):
            if not ontology.has_node(term_id):
                ontology.add_node(id=term_id, label=term_label, meta={"basicPropertyValues": [
                    {"pred": "OIO:hasOBONamespace", "val": term_type}]})

    @staticmethod
    def create_disease_annotation_record(gene_id, gene_symbol, do_term_id, ecode, prvdr):
        return {"source_line": "",
                "subject": {
                    "id": gene_id,
                    "label": gene_symbol,
                    "type": "gene",
                    "fullname": "",
                    "synonyms": [],
                    "taxon": {"id": ""}
                },
                "object": {
                    "id": do_term_id,
                    "taxon": ""
                },
                "qualifiers": "",
                "aspect": "D",
                "relation": {"id": None},
                "negated": False,
                "evidence": {
                    "type": ecode,
                    "has_supporting_reference": "",
                    "with_support_from": [],
                    "provided_by": prvdr,
                    "date": None
                }}

    @staticmethod
    def add_annotations(final_annotation_set, neo4j_annot_set, data_provider):
        for annot in neo4j_annot_set:
            ecodes = [ecode for ecode in annot["ECode"].split(", ")] if annot["relType"] != "IS_MARKER_FOR" else ["BMK"]
            for ecode in ecodes:
                final_annotation_set.append(GeneDescriptionsETL.create_disease_annotation_record(
                    annot["geneId"] if not annot["geneId"].startswith("HGNC:") else "RGD:" + annot["geneId"],
                    annot["geneSymbol"], annot["DOId"], ecode, data_provider))

    @staticmethod
    def get_disease_annotations_from_db(data_provider, gd_data_manager, key_diseases):
        annotations = []
        gene_annot_set = Neo4jHelper.run_single_parameter_query(GeneDescriptionsETL.GetGeneDiseaseAnnotQuery,
                                                                data_provider)
        GeneDescriptionsETL.add_annotations(annotations, gene_annot_set, data_provider)
        feature_annot_set = Neo4jHelper.run_single_parameter_query(GeneDescriptionsETL.GetFeatureDiseaseAnnotQuery,
                                                                   data_provider)
        allele_do_annot = defaultdict(list)
        for feature_annot in feature_annot_set:
            if all([feature_annot["geneId"] != annot[0] for annot in allele_do_annot[(feature_annot["alleleId"],
                                                                                      feature_annot["DOId"])]]):
                allele_do_annot[(feature_annot["alleleId"], feature_annot["DOId"])].append(feature_annot)
        # keep only disease annotations through simple entities (e.g., alleles related to one gene only)
        feature_annot_set = [feature_annots[0] for feature_annots in allele_do_annot.values() if
                             len(feature_annots) == 1]
        GeneDescriptionsETL.add_annotations(annotations, feature_annot_set, data_provider)
        #disease_via_orth_records = Neo4jHelper.run_single_parameter_query(
        #    GeneDescriptionsETL.GetDiseaseViaOrthologyQuery, data_provider)
        #for orth_annot in disease_via_orth_records:
        #    annotations.append(GeneDescriptionsETL.create_disease_annotation_record(
        #        gene_id=orth_annot["geneId"], gene_symbol=orth_annot["geneSymbol"], do_term_id=orth_annot["DOId"],
        #        ecode="DVO", prvdr=data_provider))
        #    if orth_annot["publicationId"] == "RGD:7240710":
        #        key_diseases[orth_annot["geneId"]].add(orth_annot["DOId"])
        return AssociationSetFactory().create_from_assocs(assocs=list(annotations),
                                                          ontology=gd_data_manager.do_ontology)

    @staticmethod
    def get_best_orthologs_from_db(data_provider):
        orthologs_set = Neo4jHelper.run_single_parameter_query(GeneDescriptionsETL.GetFilteredHumanOrthologsQuery,
                                                               data_provider)
        genes_orthologs_algos = defaultdict(lambda: defaultdict(int))
        best_orthologs = {}
        orthologs_info = {}
        for ortholog_algo in orthologs_set:
            genes_orthologs_algos[ortholog_algo["geneId"]][ortholog_algo["orthoId"]] += 1
            if ortholog_algo["orthoId"] not in orthologs_info:
                orthologs_info[ortholog_algo["orthoId"]] = (ortholog_algo["orthoSymbol"], ortholog_algo["orthoName"])
        for gene_id in genes_orthologs_algos.keys():
            best_orthologs[gene_id] = [[[ortholog_id, orthologs_info[ortholog_id][0], orthologs_info[ortholog_id][1]]
                                        for ortholog_id in genes_orthologs_algos[gene_id].keys() if
                                        genes_orthologs_algos[gene_id][ortholog_id] ==
                                        max(genes_orthologs_algos[gene_id].values())], False]
            best_orthologs[gene_id][-1] = len(best_orthologs[gene_id][0]) != len(genes_orthologs_algos[gene_id].keys())
        return best_orthologs

    @staticmethod
    def save_descriptions_report_files(data_provider, json_desc_writer):
        if "GENERATE_REPORTS" in os.environ and (os.environ["GENERATE_REPORTS"] == "True"
                                                 or os.environ["GENERATE_REPORTS"] == "true" or
                                                 os.environ["GENERATE_REPORTS"] == "pre-release"):
            gd_file_name = "HUMAN" if data_provider == "Human" else data_provider
            release_version = ".".join(os.environ["RELEASE"].split(".")[0:2]) if "RELEASE" in os.environ else \
                "no-version"
            json_desc_writer.overall_properties.species = gd_file_name
            json_desc_writer.overall_properties.release_version = release_version
            cur_date = datetime.date.today().strftime("%Y%m%d")
            json_desc_writer.overall_properties.date = cur_date
            file_name = cur_date + "_" + gd_file_name
            latest_file_name = gd_file_name + "_gene_desc_latest"
            file_path = "tmp/" + file_name
            json_desc_writer.write_json(file_path=file_path + ".json", pretty=True, include_single_gene_stats=True)
            json_desc_writer.write_plain_text(file_path=file_path + ".txt")
            json_desc_writer.write_tsv(file_path=file_path + ".tsv")
            client = boto3.client('s3', aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
                                  aws_secret_access_key=os.environ['AWS_SECRET_KEY'])
            pre_release = "/pre-release/" if os.environ["GENERATE_REPORTS"] == "pre-release" else "/release/"
            if os.environ["GENERATE_REPORTS"] == "True" or os.environ["GENERATE_REPORTS"] == "true" or \
                    os.environ["GENERATE_REPORTS"] == "pre-release":
                client.upload_file(file_path + ".json", "agr-db-reports", "gene-descriptions/" + release_version +
                                   pre_release + cur_date + "/" + file_name + ".json",
                                   ExtraArgs={'ContentType': "binary/octet-stream", 'ACL': "public-read"})
                client.upload_file(file_path + ".txt", "agr-db-reports", "gene-descriptions/" + release_version +
                                   pre_release + cur_date + "/" + file_name + ".txt",
                                   ExtraArgs={'ContentType': "binary/octet-stream", 'ACL': "public-read"})
                client.upload_file(file_path + ".tsv", "agr-db-reports", "gene-descriptions/" + release_version +
                                   pre_release + cur_date + "/" + file_name + ".tsv",
                                   ExtraArgs={'ContentType': "binary/octet-stream", 'ACL': "public-read"})
                if os.environ["GENERATE_REPORTS"] == "True" or os.environ["GENERATE_REPORTS"] == "true":
                    client.upload_file(file_path + ".json", "agr-db-reports", "gene-descriptions/" + latest_file_name +
                                       ".json", ExtraArgs={'ContentType': "binary/octet-stream", 'ACL': "public-read"})
                    client.upload_file(file_path + ".txt", "agr-db-reports", "gene-descriptions/" + latest_file_name +
                                       ".txt", ExtraArgs={'ContentType': "binary/octet-stream", 'ACL': "public-read"})
                    client.upload_file(file_path + ".tsv", "agr-db-reports", "gene-descriptions/" + latest_file_name +
                                       ".tsv", ExtraArgs={'ContentType': "binary/octet-stream", 'ACL': "public-read"})