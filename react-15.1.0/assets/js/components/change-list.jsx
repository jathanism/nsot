import React from 'react';
import {Link} from 'react-router';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';

import Menu from 'material-ui/Menu';
import MenuItem from 'material-ui/MenuItem';
import Paper from 'material-ui/Paper';
import {
  Table, TableBody, TableHeader, TableHeaderColumn, TableRow, TableRowColumn
} from 'material-ui/Table';

import {actions as changeActions} from '../change-reducers';
document.changeActions = changeActions;

// import store from '../store';

/*
import Backbone from 'backbone';
import React from 'react.backbone';
const Change = Backbone.Model.extend({
  url: 'http://localhost:8991/api/changes',
  defaults: function() {
    return {
      user: {},
      site: {},
      event: '',
      change_at: 0,
      resource: {},
      resource_id: 0
    }
  }
});
document.Change = Change;

const Changes = Backbone.Collection.extend({
  model: Change,
  url: 'http://localhost:8991/api/changes'
});
document.Changes = Changes;
export default Changes;

/////////////////
// react.backbone
/////////////////
var ChangeViewComponent = React.createBackboneClass({
  // changeOptions: "change:id",
  render: function() {
    return (
      <div>
        <h1>{this.getModel().get('id')}</h1>
      </div>
    );
  }
});

var ChangeListViewComponent = React.createBackboneClass({
  componentDidMount: function() {
    this.props.collection.fetch();
  },

  render: function() {
    var changeList = this.getCollection().map(function(change) {
      return <ChangeViewComponent model={change} key={change.id} />;
    });

    return (
      <div>
        <ul>
          {changeList}
        </ul>
      </div>
    );
  }
});

var changeCollection = new Changes();
export default changeCollection;
console.log('changeList =>', changeCollection);
var ChangeListView = React.createFactory(ChangeListViewComponent);
var ChangeListContainer = ChangeListView({collection: changeCollection});
document.ChangeListContainer = ChangeListContainer;
export default ChangeListContainer;
// react.backbone 
/////////////////
*/

// Displays a Change by hostname followed by its attributes
class ChangeView extends React.Component {
  render() {
    return (
      <TableRow>
        <TableRowColumn>
          <Link to={'/changes/' + this.props.change.id}>
            {this.props.change.id}
          </Link>
        </TableRowColumn>
        <TableRowColumn>{this.props.change.user.email}</TableRowColumn>
        <TableRowColumn>{this.props.change.event}</TableRowColumn>
        <TableRowColumn>{this.props.change.resource_name}</TableRowColumn>
        <TableRowColumn>{this.props.change.resource_id}</TableRowColumn>
        <TableRowColumn>{this.props.change.change_at}</TableRowColumn>
      </TableRow>
    );
  }
}


// Displays a list of Changes
class ChangeList extends React.Component {
  render() {
    return (
      <div>
      <h1>Changes</h1>
      <Table>
        <TableHeader displaySelectAll={false}>
          <TableRow>
            <TableHeaderColumn>ID</TableHeaderColumn>
            <TableHeaderColumn>User</TableHeaderColumn>
            <TableHeaderColumn>Event</TableHeaderColumn>
            <TableHeaderColumn>Resource Type</TableHeaderColumn>
            <TableHeaderColumn>Resource ID</TableHeaderColumn>
            <TableHeaderColumn>Change At</TableHeaderColumn>
          </TableRow>
        </TableHeader>
        <TableBody>
          {this.props.changes.map(this.createTableRow)}
        </TableBody>
      </Table>
      </div>
    );
  }

  createTableRow(change) {
    return (
      <ChangeView change={change} key={change.id} />
    );
  }
}

@connect(
  state => ({
    changes: state.changes.items
  }),
  dispatch => ({
    actions: bindActionCreators({...changeActions}, dispatch)
  })
)
class ChangeListContainer extends React.Component {
  // Load the changes and store them as a state object once the
  // response is ready.
  componentDidMount() {
    const {actions} = this.props;
    actions.fetchChanges();
  }

  render() {
    const changes = this.props.changes || [];
    return (
      // <ChangeList changes={this.state.changes} />
      <ChangeList changes={changes} />
    );
  }

}
export default ChangeListContainer;
