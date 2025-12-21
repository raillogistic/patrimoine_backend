
import graphene





#######  CampagneInventaire  #########

class CampagneInventaireCustomType(object):
    pass

#######  GroupeComptage  #########

class GroupeComptageCustomType(object):
    lieux_autorises = graphene.List("libs.graphql.schema.types.LocationType")

    def resolve_lieux_autorises(self, info):
        return self.get_lieux_autorises()

#######  EnregistrementInventaire  #########

class EnregistrementInventaireCustomType(object):
    pass
        
