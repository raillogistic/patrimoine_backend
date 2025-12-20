# # from commands.models import Command, PayableService, Convention
# import authentication
# import graphene
# from authentication.graphqls.defaults import (
#     AUTHENTICATIONMutations,
#     AUTHENTICATIONQueries,
# )
# from authentication.schema import Mutations as AuthMutations
# from authentication.schema import Query as AuthQueries
# from divers.graphqls.defaults import DIVERSMutations, DIVERSQueries
# from frontend.graphqls.defaults import (
#     FRONTENDMutations,
#     FRONTENDQueries,
# )
# from frontend.schemas import FrontendCustomMutations, FrontendCustomQueries

# # from facturation.schema import FacturationCustomMutations
# # custom
# ###
# # from reporting.graphqls.defaults import REPORTINGQueries, REPORTINGMutations
# from graphene_django.debug import DjangoDebug
# from inventory.graphqls.defaults import INVENTORYMutations, INVENTORYQueries
# from libs.graphql.mutations import LibsMutations
# from libs.reporting.mutations import Reporting

# ###
# from models.queries.models import ModelQueries, ModelsMutations
# from polymorphic.utils import reset_polymorphic_ctype
# from purchases.graphqls.defaults import PURCHASESMutations, PURCHASESQueries
# from relations.graphqls.defaults import RELATIONSMutations, RELATIONSQueries

# # from facturation.graphqls.defaults import FACTURATIONQueries, FACTURATIONMutations
# # from achat.graphqls.defaults import ACHATQueries, ACHATMutations
# # from commands.graphqls.defaults import COMMANDSQueries, COMMANDSMutations
# # from communication.graphqls.defaults import COMMUNICATIONQueries, COMMUNICATIONMutations
# # from mondat.graphqls.defaults import MONDATQueries, MONDATMutations
# from reporting.graphqls.defaults import REPORTINGMutations, REPORTINGQueries

# # Apps schemas
# from rh.graphqls.defaults import RHMutations, RHQueries
# from shrd.graphqls.defaults import SHRDMutations, SHRDQueries
# from tresorie.graphqls.defaults import TRESORIEMutations, TRESORIEQueries

# ####
# # Custom
# from tresorie.schema import CustomTresorieQueris

# from .reporting import DashboardQueries


# class Queries(
#     # Apps
#     RELATIONSQueries,
#     # ACHATQueries,
#     TRESORIEQueries,
#     # COMMANDSQueries,
#     # COMMUNICATIONQueries,
#     # MONDATQueries,
#     AUTHENTICATIONQueries,
#     REPORTINGQueries,
#     SHRDQueries,
#     RHQueries,
#     DIVERSQueries,
#     PURCHASESQueries,
#     INVENTORYQueries,
#     FRONTENDQueries,
#     # FACTURATIONQueries,
#     # ###
#     CustomTresorieQueris,
#     FrontendCustomQueries,
#     # # REPORTINGQueries,
#     DashboardQueries,
#     ModelQueries,
#     # #####
#     AuthQueries,
#     graphene.ObjectType,
# ):
#     dummy = graphene.String()
#     debug = graphene.Field(DjangoDebug, name="_debug")


# class AppMutations(
#     # app
#     RELATIONSMutations,
#     # ACHATMutations,
#     # COMMANDSMutations,
#     # MONDATMutations,
#     # COMMUNICATIONMutations,
#     REPORTINGMutations,
#     TRESORIEMutations,
#     AUTHENTICATIONMutations,
#     SHRDMutations,
#     RHMutations,
#     DIVERSMutations,
#     PURCHASESMutations,
#     INVENTORYMutations,
#     FRONTENDMutations,
#     # FACTURATIONMutations,
#     ###########
#     # Custom
#     # FacturationCustomMutations,
#     ####
#     ModelsMutations,
#     FrontendCustomMutations,
#     Reporting,
#     authentication.schema.Mutations,
#     ##### lib
#     LibsMutations,
#     graphene.ObjectType,
# ):
#     dummy_mutation = graphene.String()

#     def resolve_dummy_mutation(self, info):
#         return "ok"


# class AuthQueries(
#     # apps
#     # ProfileQuery,
#     AuthQueries,
#     graphene.ObjectType,
# ):
#     pass


# class AuthMutations(
#     AuthMutations,
#     ModelsMutations,
#     graphene.ObjectType,
# ):
#     pass


# authSchema = graphene.Schema(
#     auto_camelcase=False, query=AuthQueries, mutation=AuthMutations
# )

# schema = graphene.Schema(query=Queries, mutation=AppMutations, auto_camelcase=False)


# # from commands.models import Command, PayableService, Convention
# import authentication
# import graphene
# from authentication.graphqls.defaults import (
#     AUTHENTICATIONMutations,
#     AUTHENTICATIONQueries,
# )
# from authentication.schema import Mutations as AuthMutations
# from authentication.schema import Query as AuthQueries
# from divers.graphqls.defaults import DIVERSMutations, DIVERSQueries
# from frontend.graphqls.defaults import (
#     FRONTENDMutations,
#     FRONTENDQueries,
# )
# from frontend.schemas import FrontendCustomMutations, FrontendCustomQueries

# # from facturation.schema import FacturationCustomMutations
# # custom
# ###
# # from reporting.graphqls.defaults import REPORTINGQueries, REPORTINGMutations
# from graphene_django.debug import DjangoDebug
# from inventory.graphqls.defaults import INVENTORYMutations, INVENTORYQueries
# from libs.graphql.mutations import LibsMutations
# from libs.reporting.mutations import Reporting

# ###
# from polymorphic.utils import reset_polymorphic_ctype
# from purchases.graphqls.defaults import PURCHASESMutations, PURCHASESQueries
# from relations.graphqls.defaults import RELATIONSMutations, RELATIONSQueries

# # from facturation.graphqls.defaults import FACTURATIONQueries, FACTURATIONMutations
# # from achat.graphqls.defaults import ACHATQueries, ACHATMutations
# # from commands.graphqls.defaults import COMMANDSQueries, COMMANDSMutations
# # from communication.graphqls.defaults import COMMUNICATIONQueries, COMMUNICATIONMutations
# # from mondat.graphqls.defaults import MONDATQueries, MONDATMutations
# from reporting.graphqls.defaults import REPORTINGMutations, REPORTINGQueries

# # Apps schemas
# from rh.graphqls.defaults import RHMutations, RHQueries
# from shrd.graphqls.defaults import SHRDMutations, SHRDQueries
# from tresorie.graphqls.defaults import TRESORIEMutations, TRESORIEQueries


# ####
# # Custom
import graphene

# from authentication.graphqls.defaults import (
#     AUTHENTICATIONMutations,
#     AUTHENTICATIONQueries,
# )
# from frontend.schemas import FrontendCustomQueries
# from models.queries.models import ModelQueries, ModelsMutations
# from tresorie.schema import CustomTresorieQueris
# from .reporting import DashboardQueries
# queries = registry["ProjectQueries"]
# mutations = registry["ProjectMutations"]
# class EmptyQueriesSchema(
#     # FrontendCustomQueries,
#     # CustomTresorieQueris,
#     # FrontendCustomQueries,
#     # REPORTINGQueries,
#     # DashboardQueries,
#     # ModelQueries,
#     # AuthQueries,
#     # queries,
#     graphene.ObjectType,
# ):
#     dummy = graphene.String()
# class EmptyMutationsSchema(mutations, graphene.ObjectType):
#     dummy_mutation = graphene.String()
#     def resolve_dummy_mutation(self, info):
#         return "ok"
from authentication.schema import Mutations as AuthMutations
from authentication.schema import Query as AuthQueries

authSchema = graphene.Schema(
    auto_camelcase=False, query=AuthQueries, mutation=AuthMutations
)


# authSchema = graphene.Schema(
#     auto_camelcase=False,
#     query=EmptyQueriesSchema,
#     mutation=EmptyMutationsSchema,
# )

# schema = graphene.Schema(
#     query=EmptyQueriesSchema, mutation=EmptyMutationsSchema, auto_camelcase=False
# )
