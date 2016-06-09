import {List, Map} from 'immutable';
import {createResource, mergeReducers} from 'redux-rest-resource';

import API_ROOT from './constants';

// Device reducer
// FIXME(jathan): Having to hard-code every resource to use PATCH (upper) sucks.
const deviceResource = createResource({
  name: 'device',
  pluralName: 'devices',
  url: API_ROOT + Urls.device_detail(':id'),
  actions: {
    'update': {
      'method': 'PATCH'
    }
  }
});

// Device.interfaces reducer
const deviceInterfaceResource = createResource({
  name: 'deviceInterface',
  url: API_ROOT + Urls.device_interfaces(':id')
});

const types = {
  ...deviceResource.types,
  ...deviceInterfaceResource.types
};
const actions = {
  ...deviceResource.actions,
  ...deviceInterfaceResource.actions
};
const reducers = mergeReducers(
  deviceResource.reducers,
  {interfaces: deviceInterfaceResource.reducers}
);

export {types, actions, reducers};
