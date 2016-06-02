import { applyMiddleware, createStore, combineReducers  } from 'redux';
import {
  routerMiddleware, syncHistoryWithStore, routeReducer
} from 'react-router-redux';
import thunkMiddleware from 'redux-thunk';
import {apiMiddleware} from 'redux-api-middleware';
import createLogger from 'redux-logger';

import { reducer as formReducer } from 'redux-form';
import {browserHistory} from 'react-router';

import {reducers as deviceReducers} from './reducers';
import {changes} from './reducers';


const reducer = combineReducers(
  Object.assign({},
    {devices: deviceReducers},
    {changes},
    {form: formReducer}
  )
);

// To log all events to console (great for debugging)
const loggerMiddleware = createLogger();

// Instantiate middleware
const middleware = applyMiddleware(
  apiMiddleware, thunkMiddleware, loggerMiddleware
);

// Create the store.
const store = createStore(reducer, middleware);

export default store;
