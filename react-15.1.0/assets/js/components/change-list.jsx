import React from 'react';
import {Link} from 'react-router';
import {connect} from 'react-redux';

import Menu from 'material-ui/Menu';
import MenuItem from 'material-ui/MenuItem';
import Paper from 'material-ui/Paper';
import {
  Table, TableBody, TableHeader, TableHeaderColumn, TableRow, TableRowColumn
} from 'material-ui/Table';

import store from '../store';
import Api from '../api';


const client = new Api();


// Displays a Change by hostname followed by its attributes
class Change extends React.Component {
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
      <Change change={change} key={change.id} />
    );
  }
}


class ChangeListContainer extends React.Component {
  // Load the changes and store them as a state object once the
  // response is ready.
  componentDidMount() {
    var request = client.changes.read();
    var response = request.done((data, textStatus, xhrObject) => {
        console.log(data);
        // this.setState({changes: data});
        store.dispatch({
          type: 'CHANGE_LIST',
          changes: data
        })
      }
    );

  }

  render() {
    return (
      // <ChangeList changes={this.state.changes} />
      <ChangeList changes={this.props.changes} />
    );
  }

}

const mapStateToProps = function(store) {
  return {
    changes: store.changeState.changes
  };
}

export default connect(mapStateToProps)(ChangeListContainer)
