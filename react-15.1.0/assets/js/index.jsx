import _ from 'lodash'
import React from 'react'
import ReactDOM from 'react-dom'
import {Provider} from 'react-redux';
import Router from './router';
import store from './store';

import injectTapEventPlugin from 'react-tap-event-plugin';

// Needed for onTouchTap
// Check this repo:
// https://github.com/zilverline/react-tap-event-plugin
injectTapEventPlugin();

import App from './app'
import AtRest from 'react-at-rest'

AtRest.Store.API_PATH_PREFIX = 'http://localhost:8991/api/sites/1';
AtRest.Store.API_ENVELOPE = false;
document.Store = AtRest.Store;

/*
ReactDOM.render(
  <Provider store={store}>{Router}</Provider>,
  <App />,
  document.getElementById('react-app')
);
*/


ReactDOM.render(
  // <Provider store={store}><App /></Provider>,
  <Provider store={store}>{Router}</Provider>,
  document.getElementById('react-app')
);
