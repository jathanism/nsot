import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import { SubmissionError } from 'redux-form';

import Dialog from 'material-ui/Dialog';
import Paper from 'material-ui/Paper';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';

import store from '../store';
import {urlRedirect, refreshDevice} from '../actions';
import {actions as deviceActions} from '../reducers';
import DeviceForm from './DeviceForm';

const style = {
  margin: '16px 32px',
  padding: '16px'
}

const butt_style = {
  float: 'right'
};

class DeviceDetail extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      delete_open: false,
    }

    this.performDelete = this.performDelete.bind(this);
    this.confirmDelete = this.confirmDelete.bind(this);
    this.closeDelete = this.closeDelete.bind(this);
  }

  performDelete(event) {
    console.log('DeviceDetail.performDelete() => CLICKED', event);

    const {actions, device} = this.props;
    const promise = actions.deleteDevice(device.id);

    promise.then(resolve => (
      this.closeDelete() && actions.urlRedirect('/devices')
    ));

  }

  confirmDelete() {
    this.setState({delete_open: true});
  }

  closeDelete() {
    this.setState({delete_open: false});
    return true;
  }

  render() {
    const {device, interfaces, loading, submitForm} = this.props;
    const {actions} = this.props;


    if (loading) {
      return <Paper style={style}>Loading...</Paper>
    }

    const delete_actions = [
      <FlatButton
        label="Close"
        primary
        onTouchTap={this.closeDelete}
      />,
      <FlatButton
        label="Delete"
        secondary
        onTouchTap={this.performDelete}
      />,
    ];

    console.log('DeviceDetail.device =>', device);

    return (
      <Paper style={style}>
        <h1>{device.hostname}</h1>
        <RaisedButton
          label="Delete Device"
          secondary
          style={butt_style}
          onTouchTap={this.confirmDelete}
        />
        <DeviceForm onSubmit={submitForm} device={device} title="Update Device" />
        Device detail for id: {device.id}<br />
        Attributes: {JSON.stringify(device.attributes)}<br />
        Interfaces: {JSON.stringify(interfaces) || 'Loading...' }<br />
        <Dialog
          ref="confirmDeleteDialog"
          title="Delete Device"
          open={this.state.delete_open}
          onRequestClose={this.closeDelete}
          actions={delete_actions}
        >
          Are you sure you want to delete this device?
        </Dialog>
      </Paper>
    );
  }
}

@connect(
  state => ({
    device: state.devices.item || {},
    devices: state.devices.items,
    interfaces: state.devices.interfaces.items,
    loading: state.devices.isFetchingItem
  }),
  dispatch => ({
    actions: bindActionCreators({...deviceActions, urlRedirect, refreshDevice}, dispatch)
  })
)
export default class DeviceDetailContainer extends React.Component {
  constructor(props) {
    super(props);

    this.submitForm = this.submitForm.bind(this);
  }

  componentDidMount() {
    const {deviceId} = this.props.params;
    const {actions, device, interfaces} = this.props;

    if (deviceId) {
      if (device.id != deviceId) {
        console.log('Device not loaded, getting from API...');
        actions.getDevice(deviceId);
        actions.fetchDeviceInterfaces(deviceId);
      }
      else {
        console.log(`Device ${device.id} loaded from props!`);
        console.log(device);
      }
    }
  }

  submitForm(data) {
    const {actions, device} = this.props;
    console.log('Incoming data =', data);
    console.log('Incoming device =', device);

    // Merge existing device w/ updated form data.
    let new_device = Object.assign({}, device, data);
    console.log('Submitting merged device =>', new_device);

    var resp = actions.updateDevice(new_device);
    console.log('submitForm.resp =>', resp);

    return resp.then(function(obj) {
      console.log('Update response:', resp);
      const result = obj.body;
      console.log('Object body =>', result);
      console.log('Object context =>', obj.context);

      if ('error' in result) {
        console.log(JSON.stringify(result, null, 4));
        const error = result.error;

        const error_keys = ['hostname', 'name', '__all__'];

        let message;
        for (var idx in error_keys) {
          var error_key = error_keys[idx];
          if (error_key in error.message) {
            message = error.message[error_key];
            break;
          }
        }

        console.log('Error message =', message);
        let err = new SubmissionError(
          {hostname: message, _error: 'Device update failed!'}
        );
        console.log('SubmissionError =>', err);
        throw err;
      }
      else {
        console.log('SUCCESS: DEVICE UPDATED!');
        // Replace the new device w/ the existing props device??
        actions.refreshDevice(obj);
      }
    });
  }

  render() {
    const {device, interfaces, loading} = this.props;
    const {actions} = this.props;

    return (
      <DeviceDetail
        device={device}
        interfaces={interfaces}
        loading={loading}
        actions={actions}
        submitForm={this.submitForm}
      />
    );
  }
}
