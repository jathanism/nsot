import {createResource, mergeReducers} from 'redux-rest-resource';

import API_ROOT from './constants';

export const {types, actions, reducers} = createResource({
  name: 'change',
  pluralName: 'changes',
  url: API_ROOT + Urls.change_detail(':id')
});
