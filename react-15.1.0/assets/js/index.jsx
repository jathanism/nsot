import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';
import Router from './router';
import store from './store';

import injectTapEventPlugin from 'react-tap-event-plugin';

// Needed for onTouchTap
// Check this repo:
// https://github.com/zilverline/react-tap-event-plugin
injectTapEventPlugin();

ReactDOM.render(
  <Provider store={store}>{Router}</Provider>,
  document.getElementById('react-app')
);
