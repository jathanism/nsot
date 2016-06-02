// React Imports
import React from 'react';
import {render} from 'react-dom';
import {Link} from 'react-router';

// Material UI imports
import AppBar from 'material-ui/AppBar';
import Divider from 'material-ui/Divider';
import IconButton from 'material-ui/IconButton';
import IconMenu from 'material-ui/IconMenu';
import Menu from 'material-ui/Menu';
import MenuItem from 'material-ui/MenuItem';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import Paper from 'material-ui/Paper';
import {blue500} from 'material-ui/styles/colors';
import getMuiTheme from 'material-ui/styles/getMuiTheme';


//////////////
// Constants
//////////////
const style = {
  margin: '16px 32px',
  display: 'inline-block',
};


const NsotMenu = () => (
  <div className="menu">
    <Paper style={style}>
      <Menu>
        <MenuItem><Link to="/" activeClassName="active">Home</Link></MenuItem>
        <MenuItem><Link to="/devices" activeClassName="active">Devices</Link></MenuItem>
        <MenuItem><Link to="/networks" activeClassName="active">Networks</Link></MenuItem>
        <MenuItem><Link to="/interfaces" activeClassName="active">Interfaces</Link></MenuItem>
        <MenuItem><Link to="/attributes" activeClassName="active">Attributes</Link></MenuItem>
        <MenuItem><Link to="/changes" activeClassName="active">Changes</Link></MenuItem>
      </Menu>
    </Paper>
  </div>
);


const muiTheme = getMuiTheme({
  palette: {
    primary1Color: blue500,
  },
});


// Application object loaded by `index.jsx`
class MainLayout extends React.Component {
  render() {
    return (
      <MuiThemeProvider muiTheme={muiTheme}>
        <div>
        {/*
        <AppBar
          title="Network Source of Truth"
          iconClassNameRight="muidocs-icon-navigation-expand-more"
        />
        */}
        <div className="app">
          <header className="primary-header"></header>
          <aside className="primary-aside">
            <NsotMenu />
          </aside>
          <main>
            {this.props.children}
          </main>
        </div>
      </div>
      </MuiThemeProvider>
    );
  }
}

export default MainLayout;
