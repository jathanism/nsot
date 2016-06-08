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
// import TextField from 'material-ui/TextField';
import Dialog from 'material-ui/Dialog';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';

import { Field, reduxForm } from 'redux-form';
import { SubmissionError } from 'redux-form';
import {
  Checkbox, RadioButtonGroup, SelectField, Slider, TextField, Toggle
} from 'redux-form-material-ui';

import {createDevice, fetchDevicesIfNeeded} from '../actions';
import {urlRedirect} from '../actions';
import {actions as deviceActions} from '../reducers';
import Api from '../api';
import DeviceForm from './DeviceForm';


const client = new Api();


// Displays an attribute as "<b>key</b>: value"
class Attribute extends React.Component {
  render() {
    return (
      <div className="attribute" style={{display: 'inline-block', padding: '4px'}}>
        <b>{this.props.name}:</b> {this.props.value}
      </div>
    )
  }
}


// Displays an object's attributes in a list
class AttributeList extends React.Component {
  render() {
    var attrs = [];
    var attr_id = 0;

    for (var attr in this.props.attributes) {
      attrs.push(
        <Attribute 
          name={attr}
          value={this.props.attributes[attr]}
          key={attr + attr_id}
        />
      );
      attr_id++;
    };

    return (
      <div className="attributes">
        {attrs}
      </div>
    )
  }
}


// Displays a Device by hostname followed by its attributes
class Device extends React.Component {
  render() {
    return (
      <TableRow>
        <TableRowColumn>
          <Link to={'/devices/' + this.props.device.id}>
            {this.props.device.hostname}
          </Link>
        </TableRowColumn>
        <TableRowColumn>
          <AttributeList attributes={this.props.device.attributes} />
        </TableRowColumn>
      </TableRow>
    );
  }
}


// Displays a list of Devices
class DeviceList extends React.Component {
  render() {
    const {devices, loading, submitForm} = this.props;

    if (loading) {
      return <div><h1>Loading...</h1></div>
    }

    return (
      <div>
        <DeviceForm onSubmit={submitForm} />
        <Table>
          <TableHeader displaySelectAll={false}>
            <TableRow>
              <TableHeaderColumn>Hostname</TableHeaderColumn>
              <TableHeaderColumn>Attributes</TableHeaderColumn>
            </TableRow>
          </TableHeader>
          <TableBody>
            {devices.map(this.createTableRow)}
          </TableBody>
        </Table>
      </div>
    );
  }

  createTableRow(device) {
    return (
      <Device device={device} key={device.id} />
    );
  }
}


@connect(
  state => ({
    devices: state.devices.items,
    loading: state.devices.isFetching
  }),
  dispatch => ({
    actions: bindActionCreators({...deviceActions, urlRedirect}, dispatch)
  })
)
export default class DeviceListContainer extends React.Component {
  constructor(props) {
    super(props);

    this.submitForm = this.submitForm.bind(this);
  }

  // Load the devices and store them as a state object once the
  // response is ready.
  componentDidMount() {
    const {actions} = this.props;
    // this.props.dispatch(fetchDevicesIfNeeded());
    actions.fetchDevices();
  }

  submitForm(data) {
    // console.log('DeviceForm.props =>', this.props);
    // alert(JSON.stringify(data, null, 4));
    // this.props.dispatch(createDevice(data));
    console.log('submitForm().data =>', data);
    const {actions} = this.props;

    data.site_id = 1;  // Hack in stie_id.
    var resp = actions.createDevice(data);
    console.log('submitForm.resp =>', resp);
    return resp.then(function(obj) {

      console.log('Response:', resp);
      const result = obj.body;

      if ('error' in result) {
        console.log(JSON.stringify(result, null, 4));
        const error = result.error;

        // Potential keys for the error.
        const error_keys = ['hostname', 'name', '__all__'];

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
          {hostname: message, _error: 'Device creation failed!'}
        );
        console.log('SubmissionError =>', err);
        throw err;
      }
      else {
        actions.urlRedirect('/devices/' + result.id);
      }

    });
  }

  render() {
    const {devices, loading} = this.props;
    return (
      // <DeviceList devices={this.props.devices} submitForm={this.submitForm} />
      <DeviceList devices={devices} loading={loading} submitForm={this.submitForm} />
    );
  }

}
