import {DeliveryService, Store} from 'react-at-rest'
import React from 'react'
import DeviceListItem from './device_list_item'
import DeviceForm from './device_form'


class DeviceList extends DeliveryService {

  constructor(props) {
    super(props)

    // Create a store for accessing Devices API.
    this.DeviceStore = new Store('devices');

    // Bind event handlers
    this.handleEditDevice = this.handleEditDevice.bind(this);
    this.handleEditComplete = this.handleEditComplete.bind(this);

  }

  bindResources(props) {
    // Subscribe to all Devices via the DeviceStore
    this.subscribeAll(this.DeviceStore);
  }

  // Event handler for clicking the Edit button
  handleEditDevice(id) {
    return (e) => {
      e.preventDefault();
      this.setState({editingDevice: id});
    }
  }

  // Event handler for closing the Device form
  handleEditComplete() {
    this.setState({editingDevice: null});
  }

  renderDevices() {
    // Loop through and render all of the devices retrieved from the API.
    // Our DeviceStore stores its data in state.devices
    var devices = this.state.devices.map((device) => {
      if (device.id === this.state.editingDevice)
        return <DeviceForm
                store={this.DeviceStore}
                model={device}
                key={device.id}
                onSuccess={this.handleEditComplete} />
      else
        return <DeviceListItem
                device={device}
                key={device.id}
                onClickEdit={this.handleEditDevice} />
    });
    return devices
  }

  // Render either the "add new device" button, or the new device form
  // depending on state
  renderNewDevice() {
    if (this.state.newDevice !== true)
      return <button
              style={{marginTop: 30}}
              onClick={() => this.setState({newDevice: true})}
              className='btn btn-default'>Add New Device</button>
    else
      return (
        <div style={{marginTop: 30}}>
          <h4>Add New Device</h4>
          <DeviceForm
            store={this.DeviceStore}
            model={{}}
            onSuccess={() => this.setState({newDevice: false})} />
        </div>
      )

  }

  render() {
    // state.loaded will be true when al bound resources have finished their initial load
    if (!this.state.loaded) return <div>Loading devices...</div>

    return (
      <div className='list-group'>
        {this.renderDevices()}
        {this.renderNewDevice()}
      </div>
    )
  }

}

module.exports = DeviceList;
