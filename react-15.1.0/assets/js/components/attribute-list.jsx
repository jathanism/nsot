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

import {urlRedirect} from '../actions';
import {actions as attributeActions} from '../attribute-reducers';
import AttributeForm from './AttributeForm';

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
    const {attributes, loading, submitForm} = this.props;

    if (loading) {
      return (
        <div class="progress">
          <div class="indeterminate"></div>
        </div>
      );
    }

    return (
      <div>
        <AttributeForm onSubmit={submitForm} title="Create Attribute" />
        <Table>
          <TableHeader displaySelectAll={false} adjustForCheckbox={false}>
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
            {attributes.map(this.createTableRow)}
          </TableBody>
        </Table>
      </div>
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
    attributes: state.attributes.items,
    loading: state.attributes.isFetching
  }),
  dispatch => ({
    actions: bindActionCreators({...attributeActions, urlRedirect}, dispatch)
  })
)
class AttributeListContainer extends React.Component {
  constructor(props) {
    super(props);

    this.submitForm = this.submitForm.bind(this);
  }

  // Load the changes and store them as a state object once the
  // response is ready.
  componentDidMount() {
    const {actions} = this.props;
    actions.fetchAttributes();
  }

  submitForm(data) {
    console.log('submitForm().data =>', data);
    const {actions} = this.props;

    data.site_id = 1;  // Hack in stie_id.
    var resp = actions.createAttribute(data);
    console.log('submitForm.resp =>', resp);
    return resp.then(function(obj) {

      console.log('Response:', resp);
      const result = obj.body;

      if ('error' in result) {
        console.log(JSON.stringify(result, null, 4));
        const error = result.error;

        // Potential keys for the error.
        const error_keys = ['name', 'resource_name', '__all__'];

        let message;
        for (var idx in error_keys) {
          var error_key = error_keys[idx];
          if (error_key in error.message) {
            message = error.message[error_key];
            break;
          }
        }

        console.log('Error error =', error);
        console.log('Error message =', message);

        let err = new SubmissionError(
          {hostname: message, _error: 'Attribute creation failed!'}
        );
        console.log('SubmissionError =>', err);
        throw err;
      }
      else {
        actions.urlRedirect('/attributes/' + result.id);
      }

    });
  }

  render() {
    const {attributes, loading} = this.props;

    return (
      <AttributeList
        attributes={attributes}
        loading={loading}
        submitForm={this.submitForm}
      />
    );
  }

}
export default AttributeListContainer;
