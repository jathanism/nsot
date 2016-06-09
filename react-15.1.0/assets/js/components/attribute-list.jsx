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

import {actions as attributeActions} from '../attribute-reducers';

// Displays a Attribute
class AttributeView extends React.Component {
  render() {
    const {attribute} = this.props;

    return (
      <TableRow>
        <TableRowColumn>
          <Link to={'/attributes/' + attribute.id}>
            {attribute.name}
          </Link>
        </TableRowColumn>
        <TableRowColumn>{attribute.resource_name}</TableRowColumn>
        <TableRowColumn>{attribute.required.toString()}</TableRowColumn>
        <TableRowColumn>{attribute.multi.toString()}</TableRowColumn>
        <TableRowColumn>{attribute.display.toString()}</TableRowColumn>
        <TableRowColumn>{attribute.description}</TableRowColumn>
      </TableRow>
    );
  }
}


// Displays a list of Attributes
class AttributeList extends React.Component {
  render() {
    return (
      <Table>
        <TableHeader displaySelectAll={false}>
          <TableRow>
            <TableHeaderColumn>Name</TableHeaderColumn>
            <TableHeaderColumn>Resource Name</TableHeaderColumn>
            <TableHeaderColumn>Required</TableHeaderColumn>
            <TableHeaderColumn>Multi</TableHeaderColumn>
            <TableHeaderColumn>Display</TableHeaderColumn>
            <TableHeaderColumn>Description</TableHeaderColumn>
          </TableRow>
        </TableHeader>
        <TableBody>
          {this.props.attributes.map(this.createTableRow)}
        </TableBody>
      </Table>
    );
  }

  createTableRow(attribute) {
    return (
      <AttributeView attribute={attribute} key={attribute.id} />
    );
  }
}

@connect(
  state => ({
    attributes: state.attributes.items
  }),
  dispatch => ({
    actions: bindActionCreators({...attributeActions}, dispatch)
  })
)
class AttributeListContainer extends React.Component {
  // Load the changes and store them as a state object once the
  // response is ready.
  componentDidMount() {
    const {actions} = this.props;
    actions.fetchAttributes();
  }

  render() {
    const attributes = this.props.attributes || [];
    return (
      <AttributeList attributes={attributes} />
    );
  }

}
export default AttributeListContainer;
