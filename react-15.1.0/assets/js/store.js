import { applyMiddleware, createStore, combineReducers  } from 'redux';
import {
  routerMiddleware, syncHistoryWithStore, routeReducer
} from 'react-router-redux';
import thunkMiddleware from 'redux-thunk';
import createLogger from 'redux-logger';
import { reducer as formReducer } from 'redux-form';
import {browserHistory} from 'react-router';

import {reducers as deviceReducers} from './reducers';
import {reducers as attributeReducers} from './attribute-reducers';
import {reducers as changeReducers} from './change-reducers';


const reducer = combineReducers(
  Object.assign({},
    {devices: deviceReducers},
    {changes: changeReducers},
    {attributes: attributeReducers},
    {form: formReducer}
  )
);

// To log all events to console (great for debugging)
const loggerMiddleware = createLogger();

// Instantiate middleware
const middleware = applyMiddleware(
  thunkMiddleware, loggerMiddleware
);

// Create the store.
const store = createStore(reducer, middleware);
document.store = store;
export default store;
