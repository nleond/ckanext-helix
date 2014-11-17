import logging
import json
import time
import datetime
from ckan.lib.base import abort
from beaker.cache import (cache_regions, cache_region)
from pylons import g
from pylons.i18n import _

import ckan.model as model
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan
from ckanext.publicamundi.storers.vector import settings

resource_delete = toolkit.get_action('resource_delete')
resource_update = toolkit.get_action('resource_update')	    

@logic.side_effect_free
def new_resource_delete(context, data_dict):
    resource=ckan.model.Session.query(model.Resource).get(data_dict['id'])
    self.notify(resource,model.domain_object.DomainObjectOperation.deleted)
    res_delete = resource_delete(context, data_dict)
    
    return res_delete


''' Extend the resource_update action in order to pass the extra keys to vectorstorer resources
when they are being updated'''

resource_update = toolkit.get_action('resource_update')

@logic.side_effect_free
def new_resource_update(context, data_dict):

    resource=ckan.model.Session.query(model.Resource).get(data_dict['id']).as_dict()
    
    if resource.has_key('vectorstorer_resource'):
	if resource['format'].lower()==settings.WMS_FORMAT:
	    data_dict['parent_resource_id']=resource['parent_resource_id']
	    data_dict['vectorstorer_resource']=resource['vectorstorer_resource']
	    data_dict['wms_server']=resource['wms_server']
	    data_dict['wms_layer']=resource['wms_layer']
	if resource['format'].lower()==settings.DB_TABLE_FORMAT:
	    data_dict['vectorstorer_resource']=resource['vectorstorer_resource']
	    data_dict['parent_resource_id']=resource['parent_resource_id']
	    data_dict['geometry']=resource['geometry']
	
	if  not data_dict['url']==resource['url']:
	    abort(400 , _('You cant upload a file to a '+resource['format']+' resource.'))
    res_update = resource_update(context, data_dict)
    
    return res_update
