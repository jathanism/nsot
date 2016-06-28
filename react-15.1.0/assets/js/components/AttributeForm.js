import React from 'react';
import {Link} from 'react-router';
import {connect} from 'react-redux';

import Menu from 'material-ui/Menu';
import MenuItem from 'material-ui/MenuItem';
import Paper from 'material-ui/Paper';
import {
  Table, TableBody, TableHeader, TableHeaderColumn, TableRow, TableRowColumn
} from 'material-ui/Table';
import Dialog from 'material-ui/Dialog';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';
import { Field, reduxForm } from 'redux-form';
import {
  Checkbox, RadioButtonGroup, SelectField, Slider, TextField, Toggle
} from 'redux-form-material-ui';


class AttributeForm extends React.Component {
  constructor(props) {
    super(props);

    // Initial state
    this.state = {
      open: false,
    }

    // Bind methods
    this.handleOpen = this.handleOpen.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.performSubmit = this.performSubmit.bind(this);
  }

  handleOpen() {
    console.log('AttributeForm.handleOpen()');
    this.setState({open: true});
  }

  handleClose() {
    console.log('AttributeForm.handleClose()');
    this.setState({open: false});
  }

  performSubmit(event) {
    console.log('PERFORM SUBMIT => event', event);
    const {handleSubmit, submitFailed} = this.props;
    const promise = handleSubmit(event);

    // If the submit didn't fail, then close the dialog.
    promise.then(resolve => (
      !this.props.submitFailed && this.handleClose()
    ));

  }

  render() {
    const {
      attribute, title, error, submitFailed, handleSubmit, pristine, submitting
    } = this.props;

    console.log('AttributeForm.props =>', this.props);
    console.log('AttributeForm.dir =>', this);
    console.log('AttributeForm.props.error =>', error);
    console.log('AttributeForm.attribute =>', attribute);
    console.log('AttributeForm.refs=>', this.refs);

    return (
      <div>
        <RaisedButton
          label={title}
          primary
          style={{float: 'right'}}
          onTouchTap={this.handleOpen}
        />
        <Dialog
          ref="attributeDialog"
          title={title}
          modal={false}
          open={this.state.open}
          onRequestClose={this.handleClose}
        >
          An attribute can represent arbitrary key/value pairs.<br />
          <form onSubmit={this.performSubmit}>
            <Field
              defaultValue={attribute && attribute.name || ''}
              name="name"
              component={TextField}
              hintText="Name"
              floatingLabelText="Name"
              required
            /><br />
            <Field
              defaultValue={attribute && attribute.name || ''}
              name="resource_name"
              component={SelectField}
              hintText="Resource Type"
              floatingLabelText="Resource Type"
              required
            >
              <MenuItem value="Network" primaryText="Network" />
              <MenuItem value="Device" primaryText="Device" />
              <MenuItem value="Interface" primaryText="Interface" />
            </Field>
            <FlatButton
              label="Close"
              primary
              onTouchTap={this.handleClose}
            />
            <FlatButton
              label={title.split(' ')[0]}
              type="submit"
              primary
              keyboardFocused
              disabled={pristine || submitting}
            />
          </form>
        </Dialog>
      </div>
    );
  }
}

AttributeForm = reduxForm({
  form: 'attributeForm',
})(AttributeForm)

export default AttributeForm;
