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


// Displays an attribute as "<b>key</b>: value"
class Attribute extends React.Component {
  render() {
    return (
      <div className="attribute">
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
    /*
    var data = this.props.devices;
    var devices = Object.keys(data).map(val => data[val]);
    */

    return (
      <div>
      <h1>Devices</h1>
      <Table>
        <TableHeader displaySelectAll={false}>
          <TableRow>
            <TableHeaderColumn>Hostname</TableHeaderColumn>
            <TableHeaderColumn>Attributes</TableHeaderColumn>
          </TableRow>
        </TableHeader>
        <TableBody>
          {this.props.devices.map(this.createTableRow)}
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


class DeviceListContainer extends React.Component {
  // Load the devices and store them as a state object once the
  // response is ready.
  componentDidMount() {
    var request = client.devices.read();
    var response = request.done((data, textStatus, xhrObject) => {
        console.log(data);
        // this.setState({devices: data});
        store.dispatch({
          type: 'DEVICE_LIST',
          rows: data,
          /*
          devices: data.reduce(function(result, item) {
            result[item.id] = item;
            return result;
          }, {})
          */
        })
      }
    );

  }

  render() {
    return (
      <DeviceList devices={this.props.devices} />
    );
  }

}

const mapStateToProps = function(state) {
  return {
    devices: state.devices.rows
  };
}

export default connect(mapStateToProps)(DeviceListContainer)
