from files import *
import re

class DiseaseExt:

    def get_features(self, disease_data):
        disease_features = {}
        list_to_yield = []
        qualifier = None;

        dateProduced = disease_data['metaData']['dateProduced']
        dataProvider = disease_data['metaData']['dataProvider']
        release = None

        if 'release' in disease_data['metaData']:
            release = disease_data['metaData']['release']

        for diseaseRecord in disease_data['data']:
            if 'qualifier' in diseaseRecord:
                qualifier = diseaseRecord.get('qualifier')
            if qualifier is None:
                primaryId = diseaseRecord.get('objectId')
                print (primaryId)
                diseaseObjectType = diseaseRecord['objectRelation'].get("objectType")
                if primaryId not in disease_features:
                    disease_features[primaryId] = []
                    disease_features[primaryId].append({
                        "diseaseObjectName": diseaseRecord.get('objectName'),
                        "diseaseObjectType": diseaseObjectType,
                        "dateProduced": dateProduced,
                        "dataProvider": dataProvider})
                qualifier = None;
        return disease_features

    def get_data(self, disease_data):

        disease_annots = {}
        list_to_yield = []

        dateProduced = disease_data['metaData']['dateProduced']
        dataProvider = disease_data['metaData']['dataProvider']
        release = None

        if 'release' in disease_data['metaData']:
            release = disease_data['metaData']['release']

        for diseaseRecord in disease_data['data']:
            experimentalConditions = []
            objectRelationMap = {}
            evidenceList = []
            geneticModifiers = []
            inferredFromGeneAssociations = []
            modifier = {}
            modifierQualifier = None;
            qualifier = None;
            primaryId = diseaseRecord.get('objectId')

            if 'qualifier' in diseaseRecord:
                qualifier = diseaseRecord.get('qualifier')
            if 'evidence' in diseaseRecord:
                for evidence in diseaseRecord['evidence']:
                    pub = evidence.get('publication')
                    
                    publicationModId = pub.get('modPublicationId')
                    if publicationModId is not None:
                        localPubModId = publicationModId.split(":")[1]
                        pubModUrl= self.get_complete_pub_url(localPubModId, publicationModId)
                    if pubMedId is not None:
                        pubMedId = pub.get('pubMedId')
                        if ':' in pubMedId:
                            localPubMedId = pubMedId.split(":")[1]
                            pubMedUrl = self.get_complete_pub_url(localPubMedId, pubMedId)
                    evidenceCodes =[]
                    evidenceCodes = evidence.get('evidenceCodes')
                    evidenceList.append({"pub": pub, "pubMedId": pubMedId, "pubMedUrl": pubMedUrl, "pubModId": publicationModId, "pubModUrl": pubModUrl, "evidenceCodes": evidenceCodes})

            if 'objectRelation' in diseaseRecord:
                diseaseObjectType = diseaseRecord['objectRelation'].get("objectType")
                diseaseAssociationType = diseaseRecord['objectRelation'].get("associationType")
                
                #for gene in diseaseRecord['objectRelation']['inferredGeneAssociation']:
                #        inferredFromGeneAssociations.append(gene.get('primaryId'))
                objectRelationMap = {"diseaseObjectType": diseaseObjectType, "diseaseAssociationType": diseaseAssociationType}

            if 'experimentalConditions' in diseaseRecord:
                for experimentalCondition in diseaseRecord['experimentalConditions']:
                    experimentalConditions.append({"zecoId": experimentalCondition.get('zecoId'),
                                                   "geneOntologyId": experimentalCondition.get('geneOntologyId'),
                                                   "ncbiTaxonId": experimentalCondition.get('ncbiTaxonID'),
                                                   "chebiOntologyId": experimentalCondition.get('chebiOntologyId'),
                                                   "anatomicalId": experimentalCondition.get('anatomicalId'),
                                                   "experimentalConditionIsStandard": experimentalCondition.get(
                                                       'conditiionIsStandard'),
                                                   "freeTextCondition": experimentalCondition.get('textCondition')})
            if 'modifier' in diseaseRecord:
                associationType = diseaseRecord['modifier']['associationType']
                if 'genetic' in diseaseRecord['modifier']:
                    for geneticModifier in diseaseRecord['modifier'].get('genetic'):
                        geneticModifier.append(diseaseRecord['modifier'].get('genetic'))
                if 'experimentalConditionsText' in diseaseRecord['modifier']:
                    experimentalConditionsText = diseaseRecord['modifier'].get('experimentalConditionsText')

                modifierQualifier = diseaseRecord['modifier']['qualifier']
                modifier = {"associationType": associationType,
                            "geneticModifiers": geneticModifiers,
                            "experimentalConditionsText": experimentalConditionsText,
                            "modifierQualifier": modifierQualifier}

            if primaryId not in disease_annots:
                disease_annots[primaryId] = []
            # many fields are commented out to fulfill 0.6 requirements only, but still parse the entire file.

            if modifierQualifier is None and qualifier is None:
                disease_annots[primaryId].append({
                    "diseaseObjectName": diseaseRecord.get('objectName'),
                    "qualifier": diseaseRecord.get('qualifier'),
                    "with": diseaseRecord.get('with'),
                    "taxonId": diseaseRecord.get('taxonId'),
                    "geneticSex": diseaseRecord.get('geneticSex'),
                    "dataAssigned": diseaseRecord.get('dateAssigned'),
                    "experimentalConditions": experimentalConditions,
                    "associationType": diseaseRecord.get('objectRelation').get('associationType'),
                    "diseaseObjectType": diseaseRecord.get('objectRelation').get('objectType'),
                    #"evidenceList": evidenceList,
                    "modifier": modifier,
                    #"objectRelation": objectRelationMap,
                    "evidence": evidenceList,
                    "do_id": diseaseRecord.get('DOid'),
                    "do_name": None,
                    "dateProduced": dateProduced,
                    "release": release,
                    "dataProvider": dataProvider,
                    "doIdDisplay": {"displayId": diseaseRecord.get('DOid'), "url": "http://www.disease-ontology.org/?id=" + diseaseRecord.get('DOid'), "prefix": "DOID"}
                })
        return disease_annots

    def get_complete_pub_url(self, local_id, global_id):

        complete_url = None

        if 'MGI' in global_id:
            complete_url = 'http://www.informatics.jax.org/accession/' + global_id

        if 'RGD' in global_id:
            complete_url = 'http://rgd.mcw.edu/rgdweb/search/search.html?term=' + local_id
        if 'SGD' in global_id:
            complete_url = 'http://www.yeastgenome.org/reference/' + local_id
        if 'FB' in global_id:
            complete_url = 'http://flybase.org/reports/' + local_id + '.html'
        if 'ZFIN' in global_id:
            complete_url = 'http://zfin.org/' + local_id
        if 'WB:' in global_id:
            complete_url = 'http://www.wormbase.org/db/misc/paper?name=' + local_id
        if 'PUBMED:' in global_id:
            complete_url = 'https://www.ncbi.nlm.nih.gov/pubmed/' + local_id

        return complete_url
