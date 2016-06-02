import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';

import Paper from 'material-ui/Paper';

import store from '../store';
import {actions as deviceActions} from '../reducers';

const style = {
  margin: '16px 32px',
  padding: '16px'
}

class DeviceDetail extends React.Component {
  render() {
    // console.log('DeviceDetail => props', this.props);
    return (
      <Paper style={style}>
        <h1>{this.props.device.hostname}</h1>
        Device detail for id: {this.props.device.id}<br />
        Attributes: {JSON.stringify(this.props.device.attributes)}<br />
      </Paper>
    );
  }
}


@connect(
  state => ({device: state.devices.item || {}}),
  dispatch => ({
    actions: bindActionCreators({...deviceActions}, dispatch)
  })
)
export default class DeviceDetailContainer extends React.Component {
  componentDidMount() {
    console.log('OK REALLY?');
    const {actions} = this.props;
    if (this.props.params.deviceId) {
      if (this.props.device.id != this.props.params.deviceId) {
        console.log('Device not loaded, getting from API...');
        actions.getDevice(this.props.params.deviceId);
      }
      else {
        console.log(`Device ${this.props.device.id} loaded from props!`);
        console.log(this.props.device);
      }
    }
  }

  render() {
    return (
      <DeviceDetail device={this.props.device} />
    );
  }
}
