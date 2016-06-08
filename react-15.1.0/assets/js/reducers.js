import {List, Map} from 'immutable';
import {createResource, mergeReducers} from 'redux-rest-resource';

const API_ROOT = 'http://localhost:8991';

// Device reducer
const deviceResource = createResource({
  name: 'device',
  pluralName: 'devices',
  url: API_ROOT + Urls.device_detail(':id')
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

// Change reducer
/*
export const {types, actions, reducers} = createResource({
  name: 'change',
  url: `${API_ROOT}/changes/:id`
});
*/
