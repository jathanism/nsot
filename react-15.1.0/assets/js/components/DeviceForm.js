import React from 'react';
import {Link} from 'react-router';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';

import Menu from 'material-ui/Menu';
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


import {urlRedirect} from '../actions';
import {actions as deviceActions} from '../reducers';


class DeviceForm extends React.Component {
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
    console.log('DeviceForm.handleOpen()');
    this.setState({open: true});
  }

  handleClose() {
    console.log('DeviceForm.handleClose()');
    console.log('OPEN?', this.state.open);
    console.log('ERROR?', this.props.error);
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
      error,
      submitFailed,
      handleSubmit,
      pristine,
      submitting
    } = this.props;

    console.log('DeviceForm.props =>', this.props);
    console.log('DeviceForm.dir =>', this);
    console.log('DeviceForm.props.error =>', error);
    console.log('DeviceForm.refs=>', this.refs);

    return (
      <div>
        <RaisedButton label="Create Device" onTouchTap={this.handleOpen} />
        <Dialog
          ref="deviceDialog"
          title="Create Device"
          modal={false}
          open={this.state.open}
          onRequestClose={this.handleClose}
        >
          A device represents a node on your network.<br />
          <form onSubmit={this.performSubmit}>
            <Field
              name="hostname"
              component={TextField}
              hintText="Hostname"
              floatingLabelText="Hostname"
              required
            />
            <FlatButton
              label="Close"
              primary={true}
              onTouchTap={this.handleClose}
            />
            <FlatButton
              label="Create"
              type="submit"
              primary={true}
              keyboardFocused={true}
              disabled={pristine || submitting}
            />
          </form>
        </Dialog>
      </div>
    );
  }
}

DeviceForm = reduxForm({
  form: 'deviceForm',
})(DeviceForm)
//  returnRejectedSubmitPromise: true

export default DeviceForm;
