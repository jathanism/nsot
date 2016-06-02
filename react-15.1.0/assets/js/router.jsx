// React Imports
import React from 'react';
import {render} from 'react-dom';
import {
  Router, Route, Link, IndexRoute, browserHistory
} from 'react-router';

// Material UI imports
import AppBar from 'material-ui/AppBar';
import Divider from 'material-ui/Divider';
import IconButton from 'material-ui/IconButton';
import Menu from 'material-ui/Menu';
import MenuItem from 'material-ui/MenuItem';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import Paper from 'material-ui/Paper';
import {blue500} from 'material-ui/styles/colors';
import getMuiTheme from 'material-ui/styles/getMuiTheme';


const muiTheme = getMuiTheme({
  palette: {
    primary1Color: blue500,
  },
});


import Home from './components/home';
import MainLayout from './components/main-layout';
import ResourceLayout from './components/resource-layout';
import DeviceListContainer from './components/device-list';
import DeviceDetailContainer from './components/device-detail';
import NetworkListContainer from './components/network-list';
import NetworkDetailContainer from './components/network-detail';
import ChangeListContainer from './components/change-list';
import ChangeDetailContainer from './components/change-detail';

class PageNotFound extends React.Component {
  render() {
    return (
      <div>
        <h1>Page Not Found.</h1>
        <p>Go to <Link to="/">Home Page</Link></p>
      </div>
    )
  }
}

export default (
  <Router history={browserHistory}>
    <Route component={MainLayout}>
      <Route path="/" component={Home} />

      <Route component={ResourceLayout}>

        <Route path="devices">
          <IndexRoute component={DeviceListContainer} />
          <Route path=":deviceId" component={DeviceDetailContainer} />
        </Route>

        <Route path="networks">
          <IndexRoute component={NetworkListContainer} />
          <Route path=":networkId" component={NetworkDetailContainer} />
        </Route>

        <Route path="changes">
          <IndexRoute component={ChangeListContainer} />
          <Route path=":changeId" component={ChangeDetailContainer} />
        </Route>


      </Route>

      <Route path="*" component={PageNotFound} />

    </Route>
  </Router>
);
