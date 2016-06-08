import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';

import Dialog from 'material-ui/Dialog';
import Paper from 'material-ui/Paper';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';

import store from '../store';
import {urlRedirect} from '../actions';
import {actions as deviceActions} from '../reducers';

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
      delete_open: false
    }

    this.performDelete = this.performDelete.bind(this);
    this.confirmDelete = this.confirmDelete.bind(this);
    this.closeDelete = this.closeDelete.bind(this);
    this.performUpdate = this.performUpdate.bind(this);
  }

  performUpdate(event) {
    console.log('DeviceDetail.performUpdate() => CLICKED', event);
  }

  performDelete(event) {
    console.log('DeviceDetail.performDelete() => CLICKED', event);

    const {actions, device} = this.props;

    // alert('Actually deleting device:}' + device.id);

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
    // console.log('DeviceDetail => props', this.props);

    const {device, interfaces, loading} = this.props;
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

    return (
      <Paper style={style}>
        <h1>{device.hostname}</h1>
        <RaisedButton
          label="Delete Device"
          secondary
          style={butt_style}
          onTouchTap={this.confirmDelete}
        />
        <RaisedButton
          label="Update Device"
          primary
          style={butt_style}
          onTouchTap={this.performUpdate}
        />
        Device detail for id: {device.id}<br />
        Attributes: {JSON.stringify(device.attributes)}<br />
        Interfaces: {JSON.stringify(interfaces) || 'Loading...' }<br />
        <Dialog
          ref="confirmDeleteModal"
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
    interfaces: state.devices.interfaces.items,
    loading: state.devices.isFetchingItem
  }),
  dispatch => ({
    actions: bindActionCreators({...deviceActions, urlRedirect}, dispatch)
  })
)
export default class DeviceDetailContainer extends React.Component {
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

  render() {
    const {device, interfaces, loading} = this.props;
    const {actions} = this.props;

    return (
      <DeviceDetail
        device={device}
        interfaces={interfaces}
        loading={loading}
        actions={actions}
      />
    );
  }
}
