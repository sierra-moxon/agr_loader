"""ETL Helper."""

import uuid
import logging
from .resource_descriptor_helper_2 import ResourceDescriptorHelper2


class ETLHelper():
    """ETL Helper."""

    logger = logging.getLogger(__name__)
    rdh2 = ResourceDescriptorHelper2()
    rdh2.get_data()

    @staticmethod
    def get_cypher_xref_text():
        """Get Cypher XREF Text."""
        return """
                MERGE (id:CrossReference:Identifier {primaryKey:row.primaryKey})
                    ON CREATE SET id.name = row.id,
                     id.globalCrossRefId = row.globalCrossRefId,
                     id.localId = row.localId,
                     id.crossRefCompleteUrl = row.crossRefCompleteUrl,
                     id.prefix = row.prefix,
                     id.crossRefType = row.crossRefType,
                     id.uuid = row.uuid,
                     id.page = row.page,
                     id.primaryKey = row.primaryKey,
                     id.displayName = row.displayName

                MERGE (o)-[gcr:CROSS_REFERENCE]->(id) """

    @staticmethod
    def get_cypher_xref_tuned_text():
        """Get Cypher XREF Tuned Text."""
        return """
                MERGE (id:CrossReference:Identifier {primaryKey:row.primaryKey})
                    ON CREATE SET id.name = row.id,
                     id.globalCrossRefId = row.globalCrossRefId,
                     id.localId = row.localId,
                     id.crossRefCompleteUrl = row.crossRefCompleteUrl,
                     id.prefix = row.prefix,
                     id.crossRefType = row.crossRefType,
                     id.uuid = row.uuid,
                     id.page = row.page,
                     id.primaryKey = row.primaryKey,
                     id.displayName = row.displayName"""

    @staticmethod
    def get_publication_object_cypher_text():
        """Get Cypher Publication Text"""

        return """
             MERGE (pub:Publication {primaryKey:row.pubPrimaryKey})
                ON CREATE SET pub.pubModId = row.pubModId,
                 pub.pubMedId = row.pubMedId,
                 pub.pubModUrl = row.pubModUrl,
                 pub.pubMedUrl = row.pubMedUrl
        """

    @staticmethod
    def merge_crossref_relationships():
        """Merge Crossref Relationships."""
        return """ MERGE (o)-[gcr:CROSS_REFERENCE]->(id)"""

    @staticmethod
    def get_cypher_xref_text_interactions():
        """Get Cypger XREF Text Interactions."""
        return """
                MERGE (id:CrossReference:Identifier {primaryKey:row.primaryKey, crossRefType:row.crossRefType})
                    ON CREATE SET id.name = row.id,
                     id.globalCrossRefId = row.globalCrossRefId,
                     id.localId = row.localId,
                     id.crossRefCompleteUrl = row.crossRefCompleteUrl,
                     id.prefix = row.prefix,
                     id.crossRefType = row.crossRefType,
                     id.uuid = row.uuid,
                     id.page = row.page,
                     id.primaryKey = row.primaryKey,
                     id.displayName = row.displayName

                MERGE (o)-[gcr:CROSS_REFERENCE]->(id) """

    @staticmethod
    def get_cypher_xref_text_annotation_level():
        """Get Cypher XREF Text Annotation Level."""
        return """
                MERGE (id:CrossReference:Identifier {primaryKey:row.primaryKey})
                    SET id.name = row.id,
                     id.globalCrossRefId = row.globalCrossRefId,
                     id.localId = row.localId,
                     id.crossRefCompleteUrl = row.crossRefCompleteUrl,
                     id.prefix = row.prefix,
                     id.crossRefType = row.crossRefType,
                     id.uuid = row.uuid,
                     id.page = row.page,
                     id.primaryKey = row.primaryKey,
                     id.displayName = row.displayName,
                     id.curatedDB = apoc.convert.toBoolean(row.curatedDB),
                     id.loadedDB = apoc.convert.toBoolean(row.loadedDB)

                MERGE (o)-[gcr:ANNOTATION_SOURCE_CROSS_REFERENCE]->(id) """

    def get_expression_pub_annotation_xref(self, publication_mod_id):
        """Get Expression Pub Annotation XREF."""
        url = None
        try:
            url = self.rdh2.return_url_from_identifier(publication_mod_id)
        except KeyError:
            self.logger.critical("No reference page for %s", publication_mod_id)
        return url

    @staticmethod
    def get_xref_dict(local_id, prefix, cross_ref_type, page,
                      display_name, cross_ref_complete_url, primary_id):
        """Get XREF Dict."""
        global_xref_id = prefix + ":" + local_id
        cross_reference = {
            "id": global_xref_id,
            "globalCrossRefId": global_xref_id,
            "localId": local_id,
            "crossRefCompleteUrl": cross_ref_complete_url,
            "prefix": prefix,
            "crossRefType": cross_ref_type,
            "uuid":  str(uuid.uuid4()),
            "page": page,
            "primaryKey": primary_id,
            "displayName": display_name}

        return cross_reference

    def get_species_order(self, taxon_id):
        """Get Species Order."""
        order = None
        try:
            order = self.rdh2.get_order(taxon_id)
        except KeyError:
            self.logger.critical("Could not find order for taxon_id '%s'", taxon_id)
        return order

    def species_name_lookup(self, alt_key):
        """Lookup species name using some key.

        alt_key: can be things like Taxon_id, (i.e. NCBITaxon:9606 or 9606)
                 any case mod name (i.e. Rgd, RGD),
                 common names (i.e. rat, rno)
        """
        species_name = None
        try:
            species_name = self.rdh2.get_full_name_from_key(alt_key)
        except KeyError:
            self.logger.critical("Could not find species name for %s", alt_key)

        return species_name

    def species_lookup_by_taxonid(self, taxon_id):
        """Species Lookup by Taxon ID."""
        return self.species_name_lookup(taxon_id)

    def species_lookup_by_data_provider(self, provider):
        """Species Lookup by Data Provider."""
        return self.species_name_lookup(provider)

    def data_provider_lookup(self, species):
        """Lookup Data Provider."""
        mod = 'Alliance'
        if species == 'Homo sapiens':
            mod = 'RGD'
        else:
            try:
                mod = self.rdh2.get_key(species)
            except KeyError:
                self.logger.critical("Using default %s as %s not found", mod, species)
        return mod

    def get_complete_url_ont(self, local_id, global_id, key=None):
        """Get Complete 'ont'."""
        page = None
        if 'OMIM:PS' in global_id:
            page = 'ont'

        if not key:  # split not done before hand
            new_url = self.rdh2.return_url_from_identifier(global_id, page=page)
        else:
            new_url = self.rdh2.return_url_from_key_value(key, local_id, alt_page=page)

        return new_url

    def get_complete_pub_url(self, local_id, global_id, key=False):
        """Get Complete Pub URL.

        local_id: local value
        global_id: global_id may not be just the id part
        key: If passed we do not need to do the regular expression to get key
             most routines will have this already so just send that later on.

        """
        if 'get_complete_pub_url' not in self.rdh2.deprecated_mess:
            self.logger.info("get_complete_pub_url is Deprecated please use return_url_from_identifier")
            self.rdh2.deprecated_mess['get_complete_pub_url'] = 1
        else:
            self.rdh2.deprecated_mess['get_complete_pub_url'] += 1

        return self.rdh2.return_url_from_identifier(global_id)

    @staticmethod
    def process_identifiers(identifier):
        """Process Identifier."""
        if identifier.startswith("DRSC:"):
            # strip off DSRC prefix
            identifier = identifier.split(":", 1)[1]
        return identifier

    @staticmethod
    def add_agr_prefix_by_species_taxon(identifier, taxon_id):
        """Add AGR prefix by Species Taxon."""
        species_dict = {
            7955: 'ZFIN:',
            6239: 'WB:',
            10090: '',  # No MGI prefix
            10116: '',  # No RGD prefix
            559292: 'SGD:',
            4932: 'SGD:',
            7227: 'FB:',
            9606: '',  # No HGNC prefix
            2697049: ''  # No SARS-CoV-2 prefix
        }

        new_identifier = species_dict[taxon_id] + identifier

        return new_identifier

    def get_short_species_abbreviation(self, taxon_id):  # noqa  # will be okay after removing old method
        """Get short Species Abbreviation."""
        short_species_abbreviation = 'Alliance'
        try:
            short_species_abbreviation = self.rdh2.get_short_name(taxon_id)
        except KeyError:
            self.logger.critical("Problem looking up short species name for %s", taxon_id)

        return short_species_abbreviation

    @staticmethod
    def go_annot_prefix_lookup(dataprovider):
        """GO Annotation Prefix Lookup."""
        if dataprovider in ["MGI", "Human"]:
            return ""
        return dataprovider + ":"

    def get_mod_from_taxon(self, taxon_id):
        """Get MOD from Taxon."""
        return self.rdh2.get_key(taxon_id)

    def get_taxon_from_mod(self, mod):
        """Get Taxon From MOD."""
        return self.rdh2.get_taxon_from_key(mod)

    def get_page_complete_url(self, local_id, xref_url_map, prefix, page):
        """Get Page Complete URL."""
        if 'get_page_complete_url' not in self.rdh2.deprecated_mess:
            self.logger.info("get_page_complete_url is Deprecated please use return_url_from_key_value")
            self.rdh2.deprecated_mess['get_page_complete_url'] = 1
        else:
            self.rdh2.deprecated_mess['get_page_complete_url'] += 1
        return self.rdh2.return_url_from_key_value(prefix, local_id, alt_page=page)

    def get_expression_images_url(self, local_id, cross_ref_id, prefix):
        """Get expression Images URL."""
        if 'get_expression_images_url' not in self.rdh2.deprecated_mess:
            self.logger.info("get_expression_images_url is Deprecated please use return_url_from_key_value")
            self.rdh2.deprecated_mess['get_expression_images_url'] = 1
        else:
            self.rdh2.deprecated_mess['get_expression_images_url'] += 1
        return self.rdh2.return_url_from_key_value(prefix, local_id, alt_page='gene/expression_images')

    def get_no_page_complete_url(self, local_id, prefix, primary_id):
        """Get No Page Complete URL.

        No idea why its called get no page complete url.
        """
        if prefix.startswith('DRSC'):
            return None
        elif prefix.startswith('PANTHER'):
            page, primary_id = primary_id.split(':')
            new_url = self.rdh2.return_url_from_key_value('PANTHER', primary_id, page)
            if new_url:
                new_url = new_url.replace('PAN_BOOK', local_id)
        else:
            new_url = self.rdh2.return_url_from_key_value(prefix, local_id)
        return new_url

    # wrapper scripts to enable shortened call.
    def return_url_from_key_value(self, alt_key, value, alt_page=None):
        """Forward to rdh2."""
        return self.rdh2.return_url_from_key_value(alt_key, value, alt_page=alt_page)

    def return_url_from_identifier(self, identifier, page=None):
        """Forward to rdh2."""
        return self.rdh2.return_url_from_identifier(identifier, page=page)
