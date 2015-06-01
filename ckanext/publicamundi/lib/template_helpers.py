import operator
import datetime

import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.lib.helpers import resource_preview
from ckanext.publicamundi.lib import resource_ingestion

def filtered_list(l, key, value, op='eq'):
    '''Filter list items based on their value in a specific key/attr.
    '''

    if not l:
        return None
    
    op_map = {
        'ne': operator.ne,
        'eq': operator.eq,
        'le': operator.ge,
        'lt': operator.gt,
        'ge': operator.le,
        'gt': operator.lt,
        '!=': operator.ne,
        '==': operator.eq,
        '<=': operator.ge,
        '<':  operator.gt,
        '>=': operator.le,
        '>':  operator.lt,
        'in': operator.contains,
        'not-in': lambda a, b: not operator.contains(a, b) 
    }
   
    op = op_map.get(str(op).lower(), operator.eq)

    items_are_dicts = operator.isMappingType(l[0])
    if items_are_dicts:
        def pred(x):
            return op(value, x.get(key))
    else:
        def pred(x):
            return op(value, getattr(x, key, None))
    
    return filter(pred, l)

def get_organization_objects(org_names=[]):
    '''Fetch organizations as a dict (keyed to name) of fully-loaded objects
    '''
    
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }

    options = { 'all_fields': True }
    if org_names:
        t = type(org_names[0])
        if t is str:
            options['organizations'] = org_names
        elif t is dict:
            options['organizations'] = [org['name'] for org in org_names]

    orgs = toolkit.get_action('organization_list')(context, options)
    return { org['name']: org for org in orgs }

def resource_ingestion_result(resource_id):
    return resource_ingestion.get_result(resource_id)

def get_ingested_raster_resources(package):
    raster_resources = []
    for res in package.get('resources'):
        if res.get('rasterstorer_resource'):
            raster_resources.append(res)
    return raster_resources

def get_ingested_vector_resources(package):
    vector_resources = []
    for res in package.get('resources'):
        if res.get('vectorstorer_resource'):
            vector_resources.append(res)
    return vector_resources

_preferable_metadata_format = [
        {'name':'INSPIRE',
         'format':'xml'},
        {'name': 'CKAN',
        'format': 'json'}]

_default_metadata_format = 'xml'

# Returns the most suitable primary download format for each schema
# based on _preferable_metadata_format list of dictionaries
def get_primary_metadata_url(links, metadata_type):
    pformat = _default_metadata_format

    for mtype in _preferable_metadata_format:
        if mtype.get('name') == metadata_type:
            pformat = mtype.get('format')

    url = ''
    for link in links:
        if link.get('title') == metadata_type and link.get('format') == pformat:
            url = link.get('url')
            break
    return url

def get_ingested_raster(package,resource):
    ing_resources = []
    for res in package.get('resources'):
        if res.get('rasterstorer_resource') and res.get('parent_resource_id')==resource.get('id'):
            ing_resources.append(res)
    return ing_resources

def get_ingested_vector(package,resource):
    ing_resources = []
    for resa in package.get('resources'):
        # Ingested vector resources are derived from table which is derived from resource
        # Finding all resources that are ingested from table that is created from original resource
        if resa.get('vectorstorer_resource') and resa.get('parent_resource_id')==resource.get('id') and resa.get('format')=='data_table':
            for resb in package.get('resources'):
                if resb.get('vectorstorer_resource') and resb.get('parent_resource_id')==resa.get('id'):
                    ing_resources.append(resb)
    return ing_resources

#_previewable_formats = ['wms', 'wfs']
#def get_previewable_formats():
#    return _previewable_formats

# Returns the most suitable preview by checking whether ingested resources provide a better preview visualization

def preview_resource_or_ingested(pkg, res):
    snippet = resource_preview(pkg, res)
    if not res.get('can_be_previewed'):
        raster_resources = get_ingested_raster(pkg,res)
        vector_resources = get_ingested_vector(pkg,res)

        for ing_res in raster_resources:
            if ing_res.get('can_be_previewed'):
                snippet = resource_preview(pkg, ing_res)
                break
        for ing_res in vector_resources:
            if ing_res.get('can_be_previewed'):
                snippet = resource_preview(pkg, ing_res)
                break
    return snippet

def can_preview_resource_or_ingested(pkg, res):
    previewable = res.get('can_be_previewed')
    if not previewable:
        raster_resources = get_ingested_raster(pkg,res)
        vector_resources = get_ingested_vector(pkg,res)

        for ing_res in raster_resources:
            if ing_res.get('can_be_previewed'):
                previewable = True
                break
        for ing_res in vector_resources:
            if ing_res.get('can_be_previewed'):
                previewable = True
                break
    return previewable

