import {List, Map} from 'immutable';
import {createResource} from 'redux-rest-resource';


const API_ROOT = 'http://localhost:8991/api';


export const {types, actions, reducers} = createResource({
  name: 'device',
  url: `${API_ROOT}/devices/:id`
});


// Change reducer
const CHANGE_INITIAL = {
  rows: [],
  change: {},
};
export const changes = function(state=CHANGE_INITIAL, action) {
  switch(action.type) {
    case 'CHANGE_LIST':
      return Object.assign({}, state, {changes: action.rows});

    case 'CHANGE_DETAIL':
      return Object.assign({}, state, {change: action.change});

  }
  return state;
}
