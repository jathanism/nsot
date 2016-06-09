import {createResource, mergeReducers} from 'redux-rest-resource';

import API_ROOT from './constants';

export const {types, actions, reducers} = createResource({
  name: 'attribute',
  pluralName: 'attributes',
  url: API_ROOT + Urls.attribute_detail(':id')
});
