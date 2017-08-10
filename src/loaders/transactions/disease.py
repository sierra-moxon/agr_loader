from neo4j.v1 import GraphDatabase
from .transaction import Transaction

class DiseaseTransaction(Transaction):

    def __init__(self, graph):
        Transaction.__init__(self, graph)


    def disease_object_tx(self, data):
        '''
        Loads the Disease data into Neo4j.
        Nodes: merge object (gene, genotype, transgene, allele, etc..., merge disease term,
        '''


        query = """

            UNWIND $data as row


            FOREACH (x IN CASE WHEN row.diseaseObjectType = 'gene' THEN [1] ELSE [] END |
                //TODO: test if adding "DiseaseObject" label breaks merge
                MERGE (f:Gene {primaryKey:row.primaryId})

                MERGE (f)-[:FROM_SPECIES]->(spec)
                SET f.with = row.with

                MERGE (d:DOTerm {primaryKey:row.doId})
                SET d.doDisplayId = row.doDisplayId
                SET d.doUrl = row.doUrl
                SET d.doPrefix = row.doPrefix

                FOREACH (rel IN CASE when row.relationshipType = 'is_marker_for' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_MARKER_FOR]->(d))

                FOREACH (rel IN CASE when row.relationshipType = 'is_implicated_in' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_IMPLICATED_IN]->(d))

                FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_marker_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_MARKER_OF]->(d))

                 FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_implicated_in' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_IMPLICATED_IN]->(d))


                //Create the Association node to be used for the object/doTerm
                MERGE (da:DiseaseAssociation {primaryKey:row.diseaseAssociationId, link_from:row.primaryId, link_to:row.doId})

                //Create the relationship from the object node to association node.
                //Create the relationship from the association node to the DoTerm node.
                MERGE (f)-[fda:ASSOCIATION]->(da)
                MERGE (da)-[dad:ASSOCIATION]->(d)

                //Create nodes for other identifiers.  TODO- do this better. evidence code node needs to be linked up with each
                //of these separately.

                MERGE (pub:Publication {primaryKey:row.pubPrimaryKey})
                SET pub.pubModId = row.pubModId
                SET pub.pubMedId = row.pubMedId
                SET pub.pubModUrl = row.pubModUrl
                SET pub.pubMedUrl = row.pubMedUrl

                MERGE (da)-[dapa:ANNOTATED]->(pub)

                MERGE (ecs:EvidenceCodes {evidenceCodes:row.evidenceCodes})
                //Create Association nodes for other identifiers.
                MERGE (ecs)-[ecda:ANNOTATED]->(da)
            )

            FOREACH (x IN CASE WHEN row.diseaseObjectType = 'genotype' THEN [1] ELSE [] END |

                MERGE (f:Genotype:DiseaseObject {primaryKey:row.primaryId})

                MERGE (f)-[:FROM_SPECIES]->(spec)
                SET f.with = row.with

                MERGE (d:DOTerm {primaryKey:row.doId})
                SET d.doDisplayId = row.doDisplayId
                SET d.doUrl = row.doUrl
                SET d.doPrefix = row.doPrefix

                FOREACH (rel IN CASE when row.relationshipType = 'is_model_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_MODEL_OF]->(d))
                FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_model_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_MODEL_OF]->(d))

                //Create the Association node to be used for the object/doTerm
                MERGE (gda:Association {primaryKey:row.diseaseAssociationId, link_from:row.primaryId, link_to:row.doId})

                //Create the relationship from the object node to association node.
                //Create the relationship from the association node to the DoTerm node.
                MERGE (f)-[genoda:ASSOCIATION]->(gda)
                MERGE (gda)-[dad:ASSOCIATION]->(d)

                //Create nodes for other identifiers.  TODO- do this better. evidence code node needs to be linked up with each
                //of these separately.

                MERGE (pubg:Publication {primaryKey:row.pubPrimaryKey})
                SET pubg.pubModId = row.pubModId
                SET pubg.pubMedId = row.pubMedId
                SET pubg.pubModUrl = row.pubModUrl
                SET pubg.pubMedUrl = row.pubMedUrl

                MERGE (da)-[dapa:ANNOTATED]->(pub)

                MERGE (ecs:EvidenceCodes {evidenceCodes:row.evidenceCodes})
                //Create Association nodes for other identifiers.
                MERGE (ecs)-[ecda:ANNOTATED]->(da)

            )
            FOREACH (x IN CASE WHEN row.diseaseObjectType = 'allele' THEN [1] ELSE [] END |
                MERGE (f:Allele {primaryKey:row.primaryId})

                MERGE (f)-[:FROM_SPECIES]->(spec)
                SET f.with = row.with

                MERGE (d:DOTerm {primaryKey:row.doId})
                SET d.doDisplayId = row.doDisplayId
                SET d.doUrl = row.doUrl
                SET d.doPrefix = row.doPrefix

                FOREACH (rel IN CASE when row.relationshipType = 'is_model_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_MODEL_OF]->(d))
                FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_model_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_MODEL_OF]->(d))

                //Create the Association node to be used for the object/doTerm
                MERGE (ada:DiseaseAssociation {link_from:row.primaryId, link_to:row.doId})

                //Create the relationship from the object node to association node.
                //Create the relationship from the association node to the DoTerm node.
                MERGE (f)-[fada:ASSOCIATION]->(ada)
                MERGE (ada)-[dad:ASSOCIATION]->(d)

                MERGE (puba:Publication {primaryKey:row.pubPrimaryKey})
                SET puba.pubModId = row.pubModId
                SET puba.pubMedId = row.pubMedId
                SET puba.pubModUrl = row.pubModUrl
                SET puba.pubMedUrl = row.pubMedUrl

                MERGE (da)-[dapa:ANNOTATED]->(pub)

                MERGE (ecs:EvidenceCodes {evidenceCodes:row.evidenceCodes})
                //Create Association nodes for other identifiers.
                MERGE (ecs)-[ecda:ANNOTATED]->(da)

                FOREACH (rel IN CASE when row.relationshipType = 'is_marker_for' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_MARKER_FOR]->(d))

                FOREACH (rel IN CASE when row.relationshipType = 'is_implicated_in' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_IMPLICATED_IN]->(d))

                FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_marker_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_MARKER_OF]->(d))

                 FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_implicated_in' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_IMPLICATED_IN]->(d))


            )
            FOREACH (x IN CASE WHEN row.diseaseObjectType = 'transgene' THEN [1] ELSE [] END |
                MERGE (f:Transgene {primaryKey:row.primaryId})

                MERGE (f)-[:FROM_SPECIES]->(spec)
                SET f.with = row.with

                MERGE (d:DOTerm {primaryKey:row.doId})
                SET d.doDisplayId = row.doDisplayId
                SET d.doUrl = row.doUrl
                SET d.doPrefix = row.doPrefix

                //Create the Association node to be used for the object/doTerm
                MERGE (tda:DiseaseAssociation {link_from:row.primaryId, link_to:row.doId})

                //Create the relationship from the object node to association node.
                //Create the relationship from the association node to the DoTerm node.
                MERGE (f)-[ftda:ASSOCIATION]->(tda)
                MERGE (tda)-[dad:ASSOCIATION]->(d)

                MERGE (e:Evidence {primaryKey:row.diseaseEvidenceCodePubAssociationId, link_from:row.pubPrimaryKey, link_to:row.diseaseAssociationId})

                MERGE (ecs:EvidenceCodes {evidenceCodes:row.evidenceCodes})
                //Create Association nodes for other identifiers.
                MERGE (ecs)-[ecda:ANNOTATED]->(e)

                MERGE (tpub:Publication {primaryKey:row.pubPrimaryKey})
                SET tpub.pubModId = row.pubModId
                SET tpub.pubMedId = row.pubMedId
                SET tpub.pubModUrl = row.pubModUrl
                SET tpub.pubMedUrl = row.pubMedUrl

                MERGE (da)-[dapa:ANNOTATED]->(pub)

                MERGE (ecs:EvidenceCodes {evidenceCodes:row.evidenceCodes})
                //Create Association nodes for other identifiers.
                MERGE (ecs)-[ecda:ANNOTATED]->(da)


                FOREACH (rel IN CASE when row.relationshipType = 'is_marker_for' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_MARKER_FOR]->(d))

                FOREACH (rel IN CASE when row.relationshipType = 'is_implicated_in' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_IMPLICATED_IN]->(d))

                FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_marker_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_MARKER_OF]->(d))

                 FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_implicated_in' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_IMPLICATED_IN]->(d))


            )
            FOREACH (x IN CASE WHEN row.diseaseObjectType = 'fish' THEN [1] ELSE [] END |
                MERGE (f:Fish {primaryKey:row.primaryId})

                MERGE (f)-[:FROM_SPECIES]->(spec)
                SET f.with = row.with

                MERGE (d:DOTerm {primaryKey:row.doId})
                SET d.doDisplayId = row.doDisplayId
                SET d.doUrl = row.doUrl
                SET d.doPrefix = row.doPrefix

                //Create the Association node to be used for the object/doTerm
                MERGE (fida:DiseaseAssociation {link_from:row.primaryId, link_to:row.doId})

                //Create the relationship from the object node to association node.
                //Create the relationship from the association node to the DoTerm node.
                MERGE (f)-[ffida:ASSOCIATION]->(fida)
                MERGE (fida)-[dad:ASSOCIATION]->(d)

                //Create nodes for other identifiers.  TODO- do this better. evidence code node needs to be linked up with each
                //of these separately.

                MERGE (fpub:Publication {primaryKey:row.pubPrimaryKey})
                SET fpub.pubModId = row.pubModId
                SET fpub.pubMedId = row.pubMedId
                SET fpub.pubModUrl = row.pubModUrl
                SET fpub.pubMedUrl = row.pubMedUrl

                MERGE (e:Evidence {primaryKey:row.diseaseEvidenceCodePubAssociationId, link_from:row.pubPrimaryKey, link_to:row.diseaseAssociationId})
                MERGE (fida)-[dapa:ANNOTATED]->(fpub)
                MERGE (fida)-[dae:ANNOTATED]->(e)
                MERGE (fpub)-[fpubEv:ANNOTATED]->(e)

                MERGE (da)-[dapa:ANNOTATED]->(pub)

                MERGE (ecs:EvidenceCodes {evidenceCodes:row.evidenceCodes})
                //Create Association nodes for other identifiers.
                MERGE (ecs)-[ecda:ANNOTATED]->(da)

                FOREACH (rel IN CASE when row.relationshipType = 'is_model_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fa:IS_MODEL_OF]->(d))
                FOREACH (qualifier IN CASE when row.qualifier = 'NOT' and row.relationshipType = 'is_model_of' THEN [1] ELSE [] END |
                    MERGE (f)-[fq:IS_NOT_MODEL_OF]->(d))
            )


        """
        Transaction.execute_transaction(self, query, data)